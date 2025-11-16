import React, { useState, useRef } from 'react';

function App() {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [messages, setMessages] = useState([
    { 
      role: 'system', 
      content: 'Click "Record Question" to start a conversation.' 
    }
  ]);
  const [error, setError] = useState('');

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const audioRef = useRef(null);

  const API_URL = 'http://localhost:8000';

  const startRecording = async () => {
    try {
      setError('');
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const options = { mimeType: 'audio/webm' };
      mediaRecorderRef.current = new MediaRecorder(stream, options);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      setError('Please allow microphone access to use this feature.');
    }
  };

  const stopRecording = () => {
    return new Promise((resolve) => {
      if (mediaRecorderRef.current && isRecording) {
        mediaRecorderRef.current.onstop = () => {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          resolve(audioBlob);
        };
        mediaRecorderRef.current.stop();
        mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
        setIsRecording(false);
      }
    });
  };

  // This is the CORRECT, fixed version.
  const handleChatInteraction = async () => {
    if (isRecording) {
      const audioBlob = await stopRecording(); // <--- 1. Create audioBlob FIRST.
      if (audioBlob.size < 1000) {
        setError('Recording too short! Please say a few words.');
        return;
      }
      await sendChatMessage(audioBlob); // <--- 2. THEN use it.
    } else {
      setError('');
      startRecording();
    }
  };

  const sendChatMessage = async (audioBlob) => {
    setIsProcessing(true);
    setError('');
    
    try {
      const formData = new FormData();
      const audioFile = new File([audioBlob], 'question.webm', { type: 'audio/webm' });
      
      formData.append('audio_file', audioFile);

      console.log('Sending chat request...');

      const response = await fetch(`${API_URL}/full-interaction`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        let errorMsg = "Failed to process message";
        if (errorData.detail) {
          if (Array.isArray(errorData.detail)) {
            errorMsg = errorData.detail.map(err => err.msg).join(', ');
          } else {
            errorMsg = errorData.detail;
          }
        }
        throw new Error(errorMsg);
      }

      const userTranscript = response.headers.get('X-Transcript') || 'Processing...';
      const aiResponse = response.headers.get('X-Response-Text') || 'Responding...';

      setMessages(prev => [
        ...prev,
        { role: 'user', content: userTranscript },
        { role: 'assistant', content: aiResponse }
      ]);

      // Create a blob from the response using the server-provided content-type
      const contentType = response.headers.get('content-type') || 'audio/mpeg';
      const arrayBuffer = await response.arrayBuffer();
      console.log('Received audio from server:', { size: arrayBuffer.byteLength, contentType });

      if (arrayBuffer.byteLength === 0) {
        setError('Received empty audio from server. Check backend logs.');
        return;
      }

      const responseAudioBlob = new Blob([arrayBuffer], { type: contentType });
      const audioUrl = URL.createObjectURL(responseAudioBlob);

      if (audioRef.current) {
        audioRef.current.src = audioUrl;
        // Try autoplay; if blocked, show controls so user can start playback manually
        try {
          await audioRef.current.play();
        } catch (playErr) {
          console.warn('Autoplay blocked or playback failed:', playErr);
          setError('Audio playback blocked by browser—click play to listen.');
          audioRef.current.controls = true;
        }
        // Revoke URL after audio finishes to free memory
        audioRef.current.onended = () => {
          try {
            URL.revokeObjectURL(audioUrl);
            audioRef.current.controls = false;
          } catch (e) {
            // ignore
          }
        };
      }
    } catch (error) {
      console.error('Error in chat interaction:', error);
      setError(`Error: ${error.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <>
      <style>{`
        .App {
          text-align: center;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
          background-color: #f0f2f5;
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          color: #333;
        }

        .container {
          background-color: #ffffff;
          padding: 2rem;
          border-radius: 12px;
          box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
          width: 90%;
          max-width: 600px;
          margin: 1rem;
        }

        h1 {
          color: #1a73e8;
          font-weight: 600;
          margin-top: 0;
        }

        h2 {
          color: #555;
          border-bottom: 2px solid #f0f2f5;
          padding-bottom: 0.5rem;
          margin-top: 1.5rem;
        }

        .instructions {
          background-color: #f9f9f9;
          border: 1px solid #e0e0e0;
          border-radius: 8px;
          padding: 1rem;
          text-align: left;
          color: #555;
          line-height: 1.6;
        }

        .error-message {
          background-color: #ffebee;
          color: #c62828;
          padding: 1rem;
          border-radius: 8px;
          margin-bottom: 1rem;
          font-weight: 500;
        }

        .record-btn {
          background-color: #1a73e8;
          color: white;
          border: none;
          padding: 1rem 1.5rem;
          border-radius: 8px;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s ease;
          display: flex;
          align-items: center;
          justify-content: center;
          margin: 1.5rem auto 0;
          min-width: 250px;
        }

        .record-btn:hover {
          background-color: #1558b0;
          box-shadow: 0 4px 12px rgba(26, 115, 232, 0.3);
        }

        .record-btn:disabled {
          background-color: #b0bec5;
          cursor: not-allowed;
          box-shadow: none;
        }

        .record-btn.recording {
          background-color: #d93025;
        }

        .record-btn.recording:hover {
          background-color: #a52714;
          box-shadow: 0 4px 12px rgba(217, 48, 37, 0.3);
        }

        .recording-indicator {
          color: #d93025;
          font-weight: 600;
          margin-top: 1rem;
        }

        .pulse {
          width: 10px;
          height: 10px;
          background-color: white;
          border-radius: 50%;
          margin-right: 0.75rem;
          animation: pulse-animation 1.2s infinite ease-in-out;
        }

        @keyframes pulse-animation {
          0% { box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.7); }
          100% { box-shadow: 0 0 0 10px rgba(255, 255, 255, 0); }
        }

        .chat-section {
          width: 100%;
        }

        .messages {
          background-color: #f9f9f9;
          border: 1px solid #e0e0e0;
          border-radius: 8px;
          padding: 1rem;
          height: 300px;
          overflow-y: auto;
          text-align: left;
          margin-top: 1.5rem;
        }

        .message {
          margin-bottom: 1rem;
          line-height: 1.5;
        }

        .message.user {
          color: #333;
        }

        .message.assistant {
          color: #1a73e8;
        }
        
        .message.system {
          color: #0d8050;
          font-style: italic;
        }
      `}</style>
      <div className="App">
        <div className="container">
          <h1>🎤 Voice Chat</h1>
          
          {error && (
            <div className="error-message">
              ⚠️ {error}
            </div>
          )}
          
          <div className="chat-section">
            <h2>Voice Chat</h2>
            <p className="instructions">
              Ask questions by recording your voice. The AI will respond!
            </p>

            <div className="messages">
              {messages.map((msg, index) => (
                <div key={index} className={`message ${msg.role}`}>
                  <strong>{msg.role === 'user' ? 'You' : msg.role === 'system' ? 'System' : 'AI Assistant'}:</strong> {msg.content}
                </div>
              ))}
            </div>

            <button
              className={`record-btn ${isRecording ? 'recording' : ''}`}
              onClick={handleChatInteraction}
              disabled={isProcessing}
            >
              {isProcessing ? (
                'Processing...'
              ) : isRecording ? (
                <>
                  <span className="pulse"></span>
                  Stop Recording & Send
                </>
              ) : (
                'Record Question'
              )}
            </button>

            {isRecording && (
              <p className="recording-indicator">🔴 Recording your question...</p>
            )}

            <audio ref={audioRef} style={{ display: 'none' }} />

          </div>
        </div>
      </div>
    </>
  );
}

export default App;