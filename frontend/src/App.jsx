import { useState } from 'react'
import axios from 'axios'
import './App.css'

function App() {
  const [question, setQuestion] = useState('')
  const [images, setImages] = useState([])
  const [conversation, setConversation] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedModel, setSelectedModel] = useState('anthropic/claude-sonnet-4-5')
  const [showModelDropdown, setShowModelDropdown] = useState(false)
  const [selectedAgent, setSelectedAgent] = useState('general_agent')
  const [showAgentDropdown, setShowAgentDropdown] = useState(false)
  
  const availableModels = [
    { id: 'anthropic/claude-sonnet-4-5', name: 'Claude Sonnet 4.5', provider: 'Anthropic' },
    { id: 'openai/gpt-4o', name: 'GPT-4o', provider: 'OpenAI' }
  ]

  const availableAgents = [
    { id: 'general_agent', name: 'General Agent', emoji: '🤖', description: 'General purpose assistant' },
    { id: 'travel_agent', name: 'Travel Agent', emoji: '✈️', description: 'Travel planning assistant' },
    { id: 'self_care_agent', name: 'Self Care Agent', emoji: '💆', description: 'Health & wellness guide' },
    { id: 'capital_one_agent', name: 'Capital One Agent', emoji: '💳', description: 'Financial services helper' }
  ]

  const handleImageUpload = (e) => {
    const files = Array.from(e.target.files)
    // Append new images to existing ones
    setImages(prevImages => [...prevImages, ...files])
  }

  const removeImage = (index) => {
    setImages(prevImages => prevImages.filter((_, i) => i !== index))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!question.trim()) {
      setError('Please enter a question')
      return
    }

    // Save the current question and images
    const currentQuestion = question
    const currentImages = [...images]

    setLoading(true)
    setError(null)
    
    // Clear input for next question
    setQuestion('')
    setImages([])
    
    try {
      const formData = new FormData()
      formData.append('question', currentQuestion)
      formData.append('model', selectedModel)
      formData.append('agent', selectedAgent)
      
      // Only append images if they exist
      if (currentImages.length > 0) {
        currentImages.forEach((image, index) => {
          formData.append('images', image)
        })
      }

      const response = await axios.post('/api/analyze', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      // Add to conversation history
      setConversation(prev => [...prev, {
        question: currentQuestion,
        images: currentImages,
        answer: response.data.result,
        timestamp: new Date()
      }])
    } catch (err) {
      setError(err.response?.data?.error || 'An error occurred')
      console.error('Error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="app">
      <div className="container">
        {conversation.length === 0 && (
          <h1 className="title">inclusive</h1>
        )}
        
        {/* Conversation History */}
        <div className="conversation-history">
          {conversation.map((item, index) => (
            <div key={index} className="conversation-item">
              {/* User Question */}
              <div className="user-message">
                <div className="message-header">You asked:</div>
                {item.images.length > 0 && (
                  <div className="message-images">
                    {item.images.map((image, imgIndex) => (
                      <img 
                        key={imgIndex}
                        src={URL.createObjectURL(image)} 
                        alt={`Question ${index + 1} - Image ${imgIndex + 1}`}
                        className="message-image"
                      />
                    ))}
                  </div>
                )}
                <div className="message-text">{item.question}</div>
              </div>
              
              {/* AI Answer */}
              <div className="ai-message">
                <div className="message-header">Answer:</div>
                <div className="result-content">
                  {item.answer}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Loading State */}
        {loading && (
          <div className="loading">
            <div className="spinner"></div>
            <p>Processing your query...</p>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="error-message">
            ⚠️ {error}
          </div>
        )}

        {/* Input Section - Always at bottom */}
        <div className="input-section-fixed">
          {images.length > 0 && (
            <div className="image-preview-section">
              <div className="image-preview-grid">
                {images.map((image, index) => (
                  <div key={index} className="image-preview">
                    <img 
                      src={URL.createObjectURL(image)} 
                      alt={`Preview ${index + 1}`}
                    />
                    <button 
                      className="remove-image-btn"
                      onClick={() => removeImage(index)}
                      type="button"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="input-form">
            {/* Dropdowns above search bar */}
            <div className="dropdowns-container">
              <div className="agent-selector">
                <button
                  type="button"
                  className="agent-button"
                  onClick={() => setShowAgentDropdown(!showAgentDropdown)}
                  disabled={loading}
                >
                  <span className="agent-icon">
                    {availableAgents.find(a => a.id === selectedAgent)?.emoji}
                  </span>
                  <span className="agent-name">
                    {availableAgents.find(a => a.id === selectedAgent)?.name}
                  </span>
                  <span className="dropdown-arrow">▲</span>
                </button>
                {showAgentDropdown && (
                  <div className="agent-dropdown">
                    {availableAgents.map(agent => (
                      <button
                        key={agent.id}
                        type="button"
                        className={`agent-option ${selectedAgent === agent.id ? 'selected' : ''}`}
                        onClick={() => {
                          setSelectedAgent(agent.id)
                          setShowAgentDropdown(false)
                        }}
                      >
                        <div className="agent-option-header">
                          <span className="agent-option-emoji">{agent.emoji}</span>
                          <span className="agent-option-name">{agent.name}</span>
                        </div>
                        <div className="agent-option-description">{agent.description}</div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
              <div className="model-selector">
                <button
                  type="button"
                  className="model-button"
                  onClick={() => setShowModelDropdown(!showModelDropdown)}
                  disabled={loading}
                >
                  <span className="model-icon">🤖</span>
                  <span className="model-name">
                    {availableModels.find(m => m.id === selectedModel)?.name}
                  </span>
                  <span className="dropdown-arrow">▲</span>
                </button>
                {showModelDropdown && (
                  <div className="model-dropdown">
                    {availableModels.map(model => (
                      <button
                        key={model.id}
                        type="button"
                        className={`model-option ${selectedModel === model.id ? 'selected' : ''}`}
                        onClick={() => {
                          setSelectedModel(model.id)
                          setShowModelDropdown(false)
                        }}
                      >
                        <div className="model-option-name">{model.name}</div>
                        <div className="model-option-provider">{model.provider}</div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Search bar */}
            <div className="input-wrapper">
              <label htmlFor="file-upload" className="upload-button-inside">
                +
              </label>
              <input
                id="file-upload"
                type="file"
                multiple
                accept="image/png,image/jpeg,image/jpg,image/webp"
                onChange={handleImageUpload}
                className="file-input"
              />
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask anything..."
                className="question-input"
                disabled={loading}
              />
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default App

