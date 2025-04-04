import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import './UserDashboard.css'

function UserDashboard() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [isSharing, setIsSharing] = useState(false)
  const [customerName, setCustomerName] = useState('')
  const [conversationId, setConversationId] = useState(null)
  const [preventionTips, setPreventionTips] = useState('')
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [theme, setTheme] = useState('light');
  const [isResolved, setIsResolved] = useState(false)
  const [resolutionSteps, setResolutionSteps] = useState([])
  const mediaRecorder = useRef(null)
  const chatRef = useRef(null)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const sendMessage = async (content, type = 'text') => {
    try {
      const formData = new FormData();
      formData.append('customer_name', customerName || 'Anonymous');

      if (conversationId !== null) {
        formData.append('conversation_id', conversationId);
      }

      formData.append('message_history', JSON.stringify(messages.slice(-5))); // Send last 5 messages for context

      if (type === 'text') {
        if (!content.trim()) throw new Error('Invalid message content.');
        formData.append('message', content);
      } else {
        throw new Error('Unsupported input type.');
      }

      const userMessage = {
        type: 'user',
        content,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);

      const response = await axios.post('/api/chat/', formData);

      if (!conversationId && response.data.conversation_id) {
        setConversationId(response.data.conversation_id);
      }

      if (response.data && response.data.response) {
        const botMessage = {
          type: 'bot',
          content: response.data.response,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, botMessage]);
      } else {
        throw new Error('Invalid response format');
      }

      setInput('');
    } catch (error) {
      console.error('Error:', error);
      const fallbackMessage = {
        type: 'bot',
        content: error.response?.data?.message || "I'm sorry, something went wrong. Please try again later.",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, fallbackMessage]);
    }
  }

  const handleVoiceInput = async () => {
    try {
      if (isRecording) {
        // Stop recording immediately and close the stream.
        mediaRecorder.current.stop();
        setIsRecording(false);
      } else {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder.current = new MediaRecorder(stream);
        
        mediaRecorder.current.ondataavailable = async (e) => {
          if (e.data.size > 0) {
            // Send each chunk immediately
            await sendMessage(new Blob([e.data], { type: 'audio/wav' }), 'voice');
          }
        };

        mediaRecorder.current.onstop = () => {
          stream.getTracks().forEach(track => track.stop());
        };

        // Start recording and receive chunks every 1 second.
        mediaRecorder.current.start(1000);
        setIsRecording(true);
      }
    } catch (error) {
      console.error('Media access error:', error);
      alert('Please allow microphone access to use voice input');
    }
  }

  const handleImageUpload = async (e) => {
    const file = e.target.files[0]
    const formData = new FormData()
    formData.append('image', file)
    formData.append('customer_name', customerName || 'Anonymous')
    await sendMessage(formData, 'image')
  }

  const handleScreenShare = async () => {
    if (!isSharing) {
      const stream = await navigator.mediaDevices.getDisplayMedia()
      const video = document.createElement('video')
      video.srcObject = stream
      video.onloadedmetadata = () => {
        const canvas = document.createElement('canvas')
        canvas.width = video.videoWidth
        canvas.height = video.videoHeight
        canvas.getContext('2d').drawImage(video, 0, 0)
        const screenshot = canvas.toDataURL('image/png')
        sendMessage(screenshot, 'screenshot')
      }
      setIsSharing(true)
    }
  }

  const handlePreventionCheck = async () => {
    try {
      const response = await axios.post('/api/proactive_prevention/', {
        device_logs: 'Sample logs',
        network_status: 'Good',
        software_status: 'Up-to-date'
      });
      setPreventionTips(response.data.prevention_tips);
    } catch (error) {
      setPreventionTips('Failed to fetch prevention tips.');
    }
  };

  const handleSearch = async () => {
    try {
      const response = await axios.get(`/api/get_tickets?query=${searchQuery}`);
      setSearchResults(response.data.tickets || []);
    } catch (error) {
      console.error('Search error:', error);
      setSearchResults([]);
    }
  };

  const handleSendMessage = async (e) => {
    if (e) e.preventDefault();
    if (!input.trim()) return;
    try {
      await sendMessage(input);
      setInput('');
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleResolutionStep = async (stepIndex) => {
    const updatedSteps = resolutionSteps.map((step, idx) => ({
      ...step,
      completed: idx <= stepIndex
    }));
    setResolutionSteps(updatedSteps);
    
    if (stepIndex === resolutionSteps.length - 1) {
      setIsResolved(true);
      await axios.post('/api/chat/resolve', {
        conversationId,
        resolution: 'Issue resolved successfully'
      });
    }
  };

  return (
    <div className={`modern-chat ${theme}`}>
      <header className="chat-header">
        <h1>AI Support Assistant</h1>
        <div className="header-controls">
          <button 
            onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
            className="theme-toggle"
          >
            {theme === 'light' ? '🌙' : '☀️'}
          </button>
          <input
            type="text"
            value={customerName}
            onChange={(e) => setCustomerName(e.target.value)}
            className="name-input"
            required
          />
        </div>
      </header>

      <main className="chat-main">
        <div className="messages-container" ref={chatRef}>
          {messages.length === 0 ? (
            <div className="welcome-message">
              <h2>Welcome! 👋</h2>
              <p>How can I assist you today?</p>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div key={idx} className={`message-bubble ${msg.type}`}>
                <div className="message-content">
                  {msg.content}
                </div>
                <div className="message-meta">
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </div>
              </div>
            ))
          )}
        </div>
      </main>

      <footer className="chat-footer">
        <div className="media-buttons">
          <button 
            onClick={handleVoiceInput} 
            className={`media-btn ${isRecording ? 'recording' : ''}`}
            title="Voice input"
          >
            {isRecording ? '⬤' : '🎤'}
          </button>
          <input
            type="file"
            id="image-upload"
            accept="image/*"
            onChange={handleImageUpload}
            style={{ display: 'none' }}
          />
          <button 
            onClick={() => document.getElementById('image-upload').click()} 
            className="media-btn"
            title="Upload image"
          >
            📷
          </button>
          <button 
            onClick={handleScreenShare} 
            className={`media-btn ${isSharing ? 'sharing' : ''}`}
            title="Share screen"
          >
            {isSharing ? '⬛' : '🖥️'}
          </button>
        </div>
        <div className="text-input-container">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Message AI support..."
            className="text-input"
            autoComplete="off"
          />
          <button 
            onClick={handleSendMessage}
            className="send-btn"
            disabled={!input.trim()}
            type="button" // prevents default form submission behavior
          >
            ➤
          </button>
        </div>
      </footer>
    </div>
  )
}

export default UserDashboard
