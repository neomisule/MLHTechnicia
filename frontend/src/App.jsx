import React, { useState, useRef, useEffect } from 'react';

function App() {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [messages, setMessages] = useState([
    { 
      role: 'system', 
      content: 'Say "hey inclusive" to start a conversation.' 
    }
  ]);
  const [error, setError] = useState('');

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const audioRef = useRef(null);
  const recognitionRef = useRef(null);
  const [wakeWordDetected, setWakeWordDetected] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [liveTranscript, setLiveTranscript] = useState('');
  const [manualStartVisible, setManualStartVisible] = useState(false);
  const [audioVisible, setAudioVisible] = useState(false);
  const audioUnlockedRef = useRef(false);
  const audioContextRef = useRef(null);

  // Simple helper: normalize a string (letters only, lowercase)
  const _normalize = (s) => (s || '').toLowerCase().replace(/[^a-z]/g, '');

  // Levenshtein distance (small, adequate for short wakeword)
  const levenshtein = (a, b) => {
    const an = a.length;
    const bn = b.length;
    if (an === 0) return bn;
    if (bn === 0) return an;
    const matrix = Array.from({ length: an + 1 }, () => new Array(bn + 1).fill(0));
    for (let i = 0; i <= an; i++) matrix[i][0] = i;
    for (let j = 0; j <= bn; j++) matrix[0][j] = j;
    for (let i = 1; i <= an; i++) {
      for (let j = 1; j <= bn; j++) {
        const cost = a[i - 1] === b[j - 1] ? 0 : 1;
        matrix[i][j] = Math.min(
          matrix[i - 1][j] + 1,
          matrix[i][j - 1] + 1,
          matrix[i - 1][j - 1] + cost
        );
      }
    }
    return matrix[an][bn];
  };

  // Tolerant wake-word detector: accepts minor spelling/spacing variations
  const isWakeWordDetected = (transcript) => {
    if (!transcript) return false;
    const norm = _normalize(transcript);
    const target = _normalize(WAKE_WORD); // 'heyinclusive'

    // Quick check: contains 'hey' then 'inclusive' in order
    const idxHey = norm.indexOf('hey');
    const idxInclusive = norm.indexOf('inclusive', idxHey >= 0 ? idxHey + 1 : 0);
    if (idxHey >= 0 && idxInclusive > idxHey) return true;

    // Also check if it starts with the wake word
    if (norm.startsWith(target)) return true;

    // Fallback: edit distance to target (increased threshold for longer phrase)
    const dist = levenshtein(norm, target);
    return dist <= 4; // Increased from 2 to 4 for longer phrase
  };
  const analyserRef = useRef(null);
  const vadIntervalRef = useRef(null);
  const safetyTimeoutRef = useRef(null);
  const isStoppingRef = useRef(false);
  const recordingStartTimeRef = useRef(null);
  const WAKE_WORD = 'hey inclusive';

  useEffect(() => {
    // Start listening for the wake word automatically on mount
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setError('SpeechRecognition API not available in this browser.');
      return;
    }

    // Try to start immediately. Some browsers require a user gesture to start
    // microphone/recognition; if starting throws or fails silently, show a
    // manual start button so you can explicitly start the mic for debugging.
    try {
      startWakeWordListener();
    } catch (e) {
      console.warn('startWakeWordListener blocked, showing manual Start button', e);
      setManualStartVisible(true);
      document.addEventListener('pointerdown', () => {
        setManualStartVisible(false);
        try { startWakeWordListener(); } catch(_) {}
      }, { once: true });
    }

    return () => stopWakeWordListener();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Unlock Web Audio / autoplay via a one-time user gesture. Many browsers
  // only allow audio playback after a user gesture; we attempt to resume the
  // audio context and play a tiny silent buffer on the first gesture so
  // subsequent programmatic plays succeed.
  useEffect(() => {
    const tryUnlock = async () => {
      if (audioUnlockedRef.current) return;
      try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (!AudioCtx) {
          audioUnlockedRef.current = true;
          return;
        }
        const ctx = new AudioCtx();
        
        // CRITICAL: Resume the context if suspended (required by browser autoplay policy)
        if (ctx.state === 'suspended') {
          try {
            await ctx.resume();
          } catch (e) {
            console.warn('Failed to unlock AudioContext:', e);
            // Don't mark as unlocked if we can't resume
            try { ctx.close(); } catch (e2) {}
            return;
          }
        }
        
        // Wait a moment to ensure context is ready
        if (ctx.state !== 'running') {
          console.warn('AudioContext not running after resume, state:', ctx.state);
          try { ctx.close(); } catch (e) {}
          return;
        }
        
        // Play an inaudible buffer to satisfy autoplay policies
        const buffer = ctx.createBuffer(1, 1, ctx.sampleRate || 44100);
        const src = ctx.createBufferSource();
        src.buffer = buffer;
        const g = ctx.createGain();
        g.gain.value = 0.0;
        src.connect(g);
        g.connect(ctx.destination);
        src.start(0);
        setTimeout(() => {
          try { src.stop(); } catch (e) {}
          try { ctx.close(); } catch (e) {}
        }, 50);
        audioUnlockedRef.current = true;
      } catch (e) {
        console.warn('Audio unlock failed', e);
      }
    };

    const onGesture = () => {
      tryUnlock();
      document.removeEventListener('pointerdown', onGesture);
      document.removeEventListener('keydown', onGesture);
    };

    document.addEventListener('pointerdown', onGesture, { once: true });
    document.addEventListener('keydown', onGesture, { once: true });

    return () => {
      document.removeEventListener('pointerdown', onGesture);
      document.removeEventListener('keydown', onGesture);
    };
  }, []);

  // Helper: decode base64-encoded UTF-8 safely in browser
  const b64DecodeUnicode = (b64) => {
    if (!b64) return null;
    try {
      // Convert base64 -> binary string -> percent-encoded -> decodeURIComponent
      const binary = window.atob(b64);
      const bytes = [];
      for (let i = 0; i < binary.length; i++) {
        bytes.push('%' + ('00' + binary.charCodeAt(i).toString(16)).slice(-2));
      }
      return decodeURIComponent(bytes.join(''));
    } catch (e) {
      // Fallback: return raw atob or original string
      try { return window.atob(b64); } catch (e2) { return b64; }
    }
  };

  // Play raw ArrayBuffer audio using Web Audio API. Returns true if playback
  // started successfully (or at least scheduled) and false if it failed.
  const playArrayBufferWithAudioContext = async (arrayBuffer) => {
    try {
      // Only use Web Audio if audio is unlocked (after user gesture)
      if (!audioUnlockedRef.current) {
        return false;
      }
      
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return false;
      const ctx = new AudioCtx();
      
      // CRITICAL: Resume the context if suspended (required by browser autoplay policy)
      if (ctx.state === 'suspended') {
        try { 
          await ctx.resume(); 
        } catch (e) { 
          console.warn('Failed to resume AudioContext:', e);
          try { ctx.close(); } catch (e2) {}
          return false; // Can't play if we can't resume
        }
      }
      
      // Wait a bit to ensure context is ready
      if (ctx.state !== 'running') {
        console.warn('AudioContext not running, state:', ctx.state);
        try { ctx.close(); } catch (e) {}
        return false;
      }
      
      // decodeAudioData accepts an ArrayBuffer and returns an AudioBuffer
      const audioBuffer = await new Promise((resolve, reject) => {
        try {
          ctx.decodeAudioData(arrayBuffer.slice(0), resolve, reject);
        } catch (e) {
          // Fallback for some browsers: use decodeAudioData promise
          ctx.decodeAudioData(arrayBuffer.slice(0)).then(resolve).catch(reject);
        }
      });

      const src = ctx.createBufferSource();
      src.buffer = audioBuffer;
      const gain = ctx.createGain();
      gain.gain.value = 1.0;
      src.connect(gain);
      gain.connect(ctx.destination);
      src.start(0);

      // Ensure we close the context shortly after playback ends to free resources
      src.onended = () => {
        try { ctx.close(); } catch (e) {}
      };
      return true;
    } catch (e) {
      console.error('AudioContext playback failed', e);
      return false;
    }
  };

  const API_URL = 'http://localhost:8000';

  const startRecording = async () => {
    try {
      setError('');
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const options = { mimeType: 'audio/webm' };
      mediaRecorderRef.current = new MediaRecorder(stream, options);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      recordingStartTimeRef.current = Date.now(); // Track when recording started

      // play a short tone to indicate recording has started
      playBeep(1200, 0.05, 'sine');

      // Start VAD (voice activity detection) on the stream to auto-stop when user stops speaking
      // Use longer silence duration and lower threshold for better detection
      startVAD(stream, async () => {
        if (isStoppingRef.current) return;
        
        // Enforce minimum recording duration (1.5 seconds) to ensure we capture the question
        const recordingDuration = Date.now() - recordingStartTimeRef.current;
        const MIN_RECORDING_DURATION = 1500; // 1.5 seconds minimum
        
        if (recordingDuration < MIN_RECORDING_DURATION) {
          return; // Don't stop yet, wait for minimum duration
        }
        
        isStoppingRef.current = true;
        try {
          const audioBlob = await stopRecording();
          if (audioBlob && audioBlob.size > 0) {
            await sendChatMessage(audioBlob);
          } else {
            setError('Recording was empty.');
          }
        } catch (err) {
          console.error('Error stopping after VAD silence:', err);
        } finally {
          isStoppingRef.current = false;
          setWakeWordDetected(false);
          recordingStartTimeRef.current = null;
          // restart wake-word listener
          startWakeWordListener();
        }
      }, {
        silenceMs: 2000, // Increased from 500ms to 2000ms (2 seconds of silence required)
        silenceThreshold: 0.006, // Slightly lower threshold to be less sensitive
      });

      // Safety max duration to avoid endless recording (12s)
      safetyTimeoutRef.current = setTimeout(async () => {
        if (isStoppingRef.current) return;
        isStoppingRef.current = true;
        try {
          const audioBlob = await stopRecording();
          if (audioBlob && audioBlob.size > 0) {
            await sendChatMessage(audioBlob);
          }
        } catch (e) {
          console.error('Safety stop error', e);
        } finally {
          isStoppingRef.current = false;
          setWakeWordDetected(false);
          recordingStartTimeRef.current = null;
          startWakeWordListener();
        }
      }, 12000);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      setError('Please allow microphone access to use this feature.');
    }
  };

  const startVAD = async (stream, onSilence, {
    vadIntervalMs = 150,
    silenceThreshold = 0.006,
    silenceMs = 2000,
  } = {}) => {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) {
        console.warn('No AudioContext available for VAD');
        return;
      }
      const audioCtx = new AudioCtx();
      
      // Resume context if suspended (shouldn't happen after user gesture, but be safe)
      if (audioCtx.state === 'suspended') {
        try {
          await audioCtx.resume();
        } catch (e) {
          console.warn('Failed to resume VAD AudioContext:', e);
          try { audioCtx.close(); } catch (e2) {}
          return;
        }
      }
      
      audioContextRef.current = audioCtx;
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 2048;
      source.connect(analyser);
      analyserRef.current = analyser;

      let silenceStart = null;
      let lastSpeechTime = Date.now();
      
      vadIntervalRef.current = setInterval(() => {
        const buffer = new Float32Array(analyser.fftSize);
        analyser.getFloatTimeDomainData(buffer);
        let sum = 0.0;
        for (let i = 0; i < buffer.length; i++) {
          sum += buffer[i] * buffer[i];
        }
        const rms = Math.sqrt(sum / buffer.length);
        // Debug VAD values so we can tune thresholds in different environments

        if (rms > silenceThreshold) {
          // user is speaking
          silenceStart = null;
          lastSpeechTime = Date.now();
        } else {
          // below threshold
          if (silenceStart == null) {
            silenceStart = Date.now();
          } else {
            const elapsed = Date.now() - silenceStart;
            const timeSinceLastSpeech = Date.now() - lastSpeechTime;
            
            // Only trigger if:
            // 1. We've had enough silence (silenceMs)
            // 2. AND enough time has passed since last speech
            // 3. AND minimum recording duration has passed (checked in callback)
            if (elapsed > silenceMs && timeSinceLastSpeech > silenceMs) {
              // Detected sustained silence
              clearInterval(vadIntervalRef.current);
              vadIntervalRef.current = null;
              try {
                if (audioContextRef.current) {
                  audioContextRef.current.close();
                  audioContextRef.current = null;
                }
              } catch (e) {
                // ignore
              }
              if (typeof onSilence === 'function') {
                onSilence();
              }
            }
          }
        }
      }, vadIntervalMs);
    } catch (e) {
      console.error('startVAD error', e);
    }
  };

  const stopVAD = () => {
    try {
      if (vadIntervalRef.current) {
        clearInterval(vadIntervalRef.current);
        vadIntervalRef.current = null;
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
        audioContextRef.current = null;
      }
      analyserRef.current = null;
      if (safetyTimeoutRef.current) {
        clearTimeout(safetyTimeoutRef.current);
        safetyTimeoutRef.current = null;
      }
    } catch (e) {
      // ignore
    }
  };

  // Play a short beep using Web Audio API. Non-blocking; errors are ignored.
  const playBeep = async (freq = 750, duration = 0.06, type = 'sine') => {
    try {
      // Only play beep if audio is unlocked (after user gesture)
      if (!audioUnlockedRef.current) {
        return; // Silently skip if audio not unlocked
      }
      
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      
      // Resume context if suspended
      if (ctx.state === 'suspended') {
        try {
          await ctx.resume();
        } catch (e) {
          // If we can't resume, don't play the beep
          try { ctx.close(); } catch (e2) {}
          return;
        }
      }
      
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.type = type;
      o.frequency.value = freq;
      g.gain.value = 0.0015; // very low volume
      o.connect(g);
      g.connect(ctx.destination);
      o.start();
      // ramp down quickly to avoid clicks
      g.gain.setTargetAtTime(0, ctx.currentTime + duration * 0.8, 0.01);
      setTimeout(() => {
        try {
          o.stop();
        } catch (e) {
          // ignore
        }
        try {
          ctx.close();
        } catch (e) {
          // ignore
        }
      }, Math.max(50, duration * 1000 + 50));
    } catch (e) {
      // ignore play errors
    }
  };

  // Stop wake-word listener (SpeechRecognition)
  const stopWakeWordListener = () => {
    try {
      if (recognitionRef.current) {
        recognitionRef.current.onresult = null;
        recognitionRef.current.onerror = null;
        recognitionRef.current.onend = null;
        recognitionRef.current.stop();
        recognitionRef.current = null;
      }
    } catch (e) {
      // ignore
    }
  };

  // Start wake-word listener using Web Speech API
  const startWakeWordListener = () => {
    setError('');
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setError('SpeechRecognition API not available in this browser.');
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';
      
      // Flag to prevent processing results after wake word is detected
      let wakeWordDetectedInThisSession = false;

      recognition.onresult = (event) => {
        // Ignore all results if wake word was already detected
        if (wakeWordDetectedInThisSession) {
          return;
        }
        
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const res = event.results[i];
          const transcriptRaw = res[0].transcript;
          const transcript = transcriptRaw.toLowerCase().trim();
          
          // Check both interim and final results for faster detection
          const normalizedTranscript = _normalize(transcript);
          const wakeWordNormalized = _normalize(WAKE_WORD);
          
          // For "hey inclusive", be more flexible with detection
          // Check multiple patterns:
          // 1. Exact match (starts with "heyinclusive")
          // 2. Starts with "hey" followed by "inclusive" anywhere after
          // 3. Contains "hey" and "inclusive" in order
          const startsWithHey = normalizedTranscript.indexOf('hey') === 0;
          const hasInclusive = normalizedTranscript.indexOf('inclusive') >= 0;
          const hasInclusiveAfterHey = normalizedTranscript.indexOf('inclusive', 3) > 0;
          
          // More lenient detection for longer phrase
          const startsWithWakeWord = 
            normalizedTranscript.startsWith(wakeWordNormalized) ||
            (startsWithHey && hasInclusiveAfterHey) ||
            (startsWithHey && hasInclusive && normalizedTranscript.length >= wakeWordNormalized.length - 2) ||
            isWakeWordDetected(transcript); // Use the wake word detector function
          
          
          if (startsWithWakeWord && !wakeWordDetectedInThisSession) {
            // Detected wake word at start — stop immediately
            wakeWordDetectedInThisSession = true;
            setWakeWordDetected(true);
            
            // Stop recognition immediately
            try {
              recognition.stop();
            } catch (e) {
              // ignore
            }
            
            stopWakeWordListener();
            setIsListening(false);
            setLiveTranscript('');
            
            // play subtle feedback to confirm wake
            playBeep(1100, 0.03, 'sine');

            // Start recording ASAP to capture the user's question
            // Reduced delay to capture more of the user's speech
            setTimeout(() => {
              startRecording();
            }, 200); // Reduced delay to capture more audio

            // Legacy safety stop (kept as fallback) — VAD will normally handle stop.
            const MAX_MS = 8000;
            setTimeout(async () => {
              if (isStoppingRef.current) return;
              isStoppingRef.current = true;
              try {
                const audioBlob = await stopRecording();
                if (audioBlob && audioBlob.size > 0) {
                  await sendChatMessage(audioBlob);
                } else {
                  setError('Recording was empty.');
                }
              } catch (err) {
                console.error('Error stopping after wake word:', err);
              } finally {
                isStoppingRef.current = false;
                setWakeWordDetected(false);
                // Restart wake-word listener
                startWakeWordListener();
              }
            }, MAX_MS);

            break; // Exit loop once wake word is detected
          } else if (res.isFinal) {
            // Not a wake word, just update live transcript for display (only on final)
            setLiveTranscript(transcript);
          } else {
            // Interim result - update live transcript
            setLiveTranscript(transcript);
          }
        }
      };

      recognition.onerror = (e) => {
        // Don't log 'no-speech' errors as they're common and not real errors
        if (e.error !== 'no-speech' && e.error !== 'aborted') {
          console.warn('SpeechRecognition error:', e.error, e);
        }
        // If there's a serious error, restart the listener
        if (e.error === 'not-allowed' || e.error === 'service-not-allowed') {
          setError('Microphone access denied. Please allow microphone access.');
        }
      };

      recognition.onend = () => {
        // mark not listening and restart recognition (some browsers stop it intermittently)
        setIsListening(false);
        setTimeout(() => startWakeWordListener(), 500);
      };

      recognition.start();
      recognitionRef.current = recognition;
      setIsListening(true);
      // subtle feedback so user knows the app started listening
      playBeep(900, 0.04, 'triangle');
      setManualStartVisible(false);
    } catch (e) {
      console.error('Failed to start SpeechRecognition:', e);
      setError('Failed to start voice trigger.');
    }
  };

  const stopRecording = () => {
    return new Promise((resolve) => {
      // Always attempt to stop/cleanup and resolve. If nothing to stop, resolve null.
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.onstop = () => {
          try {
            const totalChunks = audioChunksRef.current.length;
            let totalBytes = 0;
            for (const c of audioChunksRef.current) {
              if (c && c.size) totalBytes += c.size;
            }
            const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
            // cleanup VAD and safety timers
            stopVAD();
            recordingStartTimeRef.current = null; // Reset recording start time
            resolve(audioBlob);
          } catch (e) {
            console.error('Error constructing audio blob on stop', e);
            stopVAD();
            resolve(null);
          }
        };
        try {
          mediaRecorderRef.current.stop();
        } catch (e) {
          console.warn('Error calling mediaRecorder.stop()', e);
        }
        try {
          if (mediaRecorderRef.current.stream && mediaRecorderRef.current.stream.getTracks) {
            mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
          }
        } catch (e) {
          // ignore
        }
        setIsRecording(false);
      } else {
        // Nothing was recording; ensure VAD/safety are cleaned up
        stopVAD();
        recordingStartTimeRef.current = null; // Reset recording start time
        resolve(null);
      }
    });
  };

  // No manual trigger: wake-word listening runs automatically.

  const sendChatMessage = async (audioBlob) => {
    setIsProcessing(true);
    setError('');
    
    try {
      const formData = new FormData();
      const audioFile = new File([audioBlob], 'question.webm', { type: 'audio/webm' });
      
      formData.append('audio_file', audioFile);


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

      // Try base64 headers first (backend encodes Unicode safely). Fallback
      // to legacy headers if present.
      const transcriptB64 = response.headers.get('X-Transcript-B64');
      const responseB64 = response.headers.get('X-Response-Text-B64');
      const legacyTranscript = response.headers.get('X-Transcript');
      const legacyResponse = response.headers.get('X-Response-Text');

      const userTranscript = transcriptB64 ? b64DecodeUnicode(transcriptB64) : (legacyTranscript || 'Processing...');
      const aiResponse = responseB64 ? b64DecodeUnicode(responseB64) : (legacyResponse || 'Responding...');

      setMessages(prev => [
        ...prev,
        { role: 'user', content: userTranscript },
        { role: 'assistant', content: aiResponse }
      ]);

      // Create a blob from the response using the server-provided content-type
      const contentType = response.headers.get('content-type') || 'audio/mpeg';
      const arrayBuffer = await response.arrayBuffer();

      if (arrayBuffer.byteLength === 0) {
        setError('Received empty audio from server. Check backend logs.');
        return;
      }

      const responseAudioBlob = new Blob([arrayBuffer], { type: contentType });
      const audioUrl = URL.createObjectURL(responseAudioBlob);

      // ALWAYS show the audio player - make it visible immediately
      setAudioVisible(true); // Set visible FIRST so the element renders

      // Wait a moment for React to render the audio element, then set it up
      setTimeout(() => {
        // Always show the audio player with controls - HTML5 audio is more reliable
        if (!audioRef.current) {
          console.error('❌ Audio element ref is null! Cannot play audio.');
          setError('Audio player not initialized. Please refresh the page.');
          URL.revokeObjectURL(audioUrl);
          return;
        }

        try {
          // Set up audio element
          audioRef.current.src = audioUrl;
          audioRef.current.volume = 1.0;
          audioRef.current.controls = true;  // Always show controls
          audioRef.current.muted = false;

        // Add error handler for audio loading/playback issues
        audioRef.current.onerror = (e) => {
          console.error('❌ Audio element error:', e);
          const error = audioRef.current?.error;
          if (error) {
            let errorMsg = 'Audio playback error: ';
            switch (error.code) {
              case error.MEDIA_ERR_ABORTED:
                errorMsg += 'Playback aborted';
                break;
              case error.MEDIA_ERR_NETWORK:
                errorMsg += 'Network error';
                break;
              case error.MEDIA_ERR_DECODE:
                errorMsg += 'Decode error - audio format may not be supported';
                break;
              case error.MEDIA_ERR_SRC_NOT_SUPPORTED:
                errorMsg += 'Audio format not supported';
                break;
              default:
                errorMsg += `Error code ${error.code}`;
            }
            console.error(errorMsg);
            setError('Audio playback failed. Please try again.');
          }
        };

        // Load the audio first, then try to play
        audioRef.current.load(); // Ensure audio is loaded
        
        // Try autoplay - this is the primary playback method
        const playAudio = async () => {
          if (!audioRef.current) {
            console.error('❌ Audio element disappeared before playback');
            return;
          }
          
          try {
            const playPromise = audioRef.current.play();
            if (playPromise !== undefined) {
              await playPromise;
              setError(''); // Clear any previous errors
            }
          } catch (playErr) {
            console.warn('⚠️ Autoplay blocked - user can click play button:', playErr);
            // Show a message to user that they can click play
            setError('Audio ready! Click the play button to hear the response.');
          }
        };
        
        // Small delay to ensure audio is loaded
        setTimeout(() => {
          playAudio();
        }, 100);

        // Revoke URL after audio finishes to free memory
        audioRef.current.onended = () => {
          try {
            URL.revokeObjectURL(audioUrl);
            // Keep controls visible for a moment, then hide
            setTimeout(() => {
              if (audioRef.current) {
                audioRef.current.controls = false;
                setAudioVisible(false);
              }
            }, 1000);
          } catch (e) {
            console.error('Error in onended handler:', e);
          }
        };
        
        // Also listen for play events to confirm it's playing
        audioRef.current.onplay = () => {
          setError(''); // Clear any error messages
        };

        // Listen for when audio can play (loaded and ready)
        audioRef.current.oncanplay = () => {
        };
        } catch (e) {
          console.error('❌ Error setting up audio element:', e);
          setError(`Error setting up audio: ${e.message}`);
          URL.revokeObjectURL(audioUrl);
        }
      }, 50); // Small delay to ensure React has rendered the audio element

      // Try Web Audio API as a fallback ONLY if HTML5 audio fails
      // But don't rely on it since it's less reliable for autoplay
      setTimeout(async () => {
        // Only try Web Audio if HTML5 audio didn't start playing
        if (audioRef.current && audioRef.current.paused && audioUnlockedRef.current) {
          try {
            const played = await playArrayBufferWithAudioContext(arrayBuffer);
            if (played) {
            }
          } catch (e) {
          }
        }
      }, 500);
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

        .listening-pulse {
          width: 14px;
          height: 14px;
          background: #1a73e8;
          border-radius: 50%;
          box-shadow: 0 0 0 rgba(26,115,232,0.7);
          animation: listening-pulse 1.4s infinite ease-out;
        }

        @keyframes listening-pulse {
          0% { box-shadow: 0 0 0 0 rgba(26,115,232,0.7); transform: scale(1); }
          50% { box-shadow: 0 0 0 10px rgba(26,115,232,0.12); transform: scale(1.05); }
          100% { box-shadow: 0 0 0 0 rgba(26,115,232,0); transform: scale(1); }
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


            <div style={{ marginTop: '1rem' }}>
              <p style={{ margin: 0 }}>Say <strong>"hey inclusive"</strong> to start recording. If you don't hear the mic prompt, click anywhere on the page to allow microphone access.</p>
                  {isListening && !isRecording && (
                    <div style={{ display: 'flex', justifyContent: 'center', marginTop: 8 }}>
                      <span className="listening-pulse" aria-hidden="true" title="Listening"></span>
                    </div>
                  )}
              {!('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) && (
                <p style={{ color: '#b00', marginTop: '0.5rem' }}>
                  Voice trigger not supported in this browser — the app will not listen automatically.
                </p>
              )}
            </div>

            {(isRecording || wakeWordDetected) && (
              <p className="recording-indicator">🔴 Recording your question...</p>
            )}

            {/* Audio player - always visible when audio is available */}
            {audioVisible && (
              <div style={{ 
                marginTop: '1rem', 
                padding: '1.5rem',
                background: '#f0f7ff',
                borderRadius: '8px',
                border: '2px solid #1a73e8',
                boxShadow: '0 2px 8px rgba(26, 115, 232, 0.2)'
              }}>
                <p style={{ margin: '0 0 1rem 0', fontWeight: 600, color: '#1a73e8', fontSize: '1.1rem' }}>
                  🔊 AI Response Audio
                </p>
                <audio 
                  ref={audioRef} 
                  controls 
                  style={{ 
                    width: '100%',
                    display: 'block',
                    marginBottom: '1rem'
                  }} 
                />
                {/* Manual play button as fallback */}
                <button
                  onClick={() => {
                    if (audioRef.current) {
                      audioRef.current.play().catch(e => {
                        console.error('Manual play failed:', e);
                        setError('Could not play audio. Please check browser permissions.');
                      });
                    }
                  }}
                  style={{
                    width: '100%',
                    padding: '0.75rem 1.5rem',
                    backgroundColor: '#1a73e8',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    fontSize: '1rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    transition: 'background-color 0.2s'
                  }}
                  onMouseOver={(e) => e.target.style.backgroundColor = '#1558b0'}
                  onMouseOut={(e) => e.target.style.backgroundColor = '#1a73e8'}
                >
                  ▶️ Play Response
                </button>
              </div>
            )}

          </div>
        </div>
      </div>
    </>
  );
}

export default App;