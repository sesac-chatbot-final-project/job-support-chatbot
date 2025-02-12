import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import "bootstrap/dist/css/bootstrap.min.css";
import "../styles.css";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faAngleRight,
  faUserCircle,
  faCog,
  faMicrophone,
  faStopCircle,
} from "@fortawesome/free-solid-svg-icons";

// Custom hook for auto-scrolling
const useAutoScroll = (dependency) => {
  const scrollRef = useRef(null);
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [dependency]);
  return scrollRef;
};

// Progress Bar Component using Bootstrap styles
const ProgressBar = () => (
  <div className="progress mt-4" style={{ height: "4px" }}>
    <div
      className="progress-bar progress-bar-striped progress-bar-animated"
      role="progressbar"
      style={{ width: "100%" }}
    />
  </div>
);

// Regular expression for URL detection
const urlRegex = /(https?:\/\/[^\s]+)/g;

const Chatbot = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);
  const navigate = useNavigate();
  const scrollRef = useAutoScroll(messages);

  // ===== 음성(STT) 관련 상태 및 ref =====
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [transcription, setTranscription] = useState("");
  const mediaRecorderRef = useRef(null);
  // ======================================

  // Ref to ensure the initial messages are set only once
  const didInit = useRef(false);

  // Function to process text and convert URLs to clickable links
  const processMessage = (text) => {
    if (typeof text !== "string") return text;
    const parts = text.split(urlRegex);
    return parts.map((part, index) => {
      if (part.match(urlRegex)) {
        return (
          <a
            key={index}
            href={part}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline"
          >
            {part}
          </a>
        );
      }
      return part;
    });
  };

  // Adds a bot message to the chat
  const displayBotMessage = (message) => {
    if (!message?.trim()) {
      message = "죄송합니다. 응답을 생성하는 중 오류가 발생했습니다.";
    }
    setMessages((prev) => [
      ...prev,
      {
        sender: "bot",
        text: processMessage(
          message.split("\n").map((line, index) => (
            <React.Fragment key={index}>
              {line}
              <br />
            </React.Fragment>
          ))
        ),
        timestamp: new Date().toISOString(),
      },
    ]);
  };

  // Adds a user message to the chat
  const displayUserMessage = (message) => {
    if (!message?.trim()) return;
    setMessages((prev) => [
      ...prev,
      {
        sender: "user",
        text: processMessage(message),
        timestamp: new Date().toISOString(),
      },
    ]);
  };

  // Initialize chat with welcome messages only once
  useEffect(() => {
    if (didInit.current) return;
    didInit.current = true;
    const initialMessages = [
      "안녕하세요! 저는 취업 지원 서비스 챗봇입니다. 원하는 서비스를 선택해주세요!",
      "1. 채용 공고 탐색\n2. 자기소개서 작성\n3. 면접 연습",
    ];
    setMessages(
      initialMessages.map((msg) => ({
        sender: "bot",
        text: processMessage(msg),
        timestamp: new Date().toISOString(),
      }))
    );
  }, []);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Responsive container width (max 1900px)
  const getResponsiveWidth = () => {
    return `${Math.min(windowWidth, 1900)}px`;
  };

  // Generates a local bot response based on user input keywords
  const generateBotResponse = (userInput) => {
    const keywords = {
      1: "채용 공고 탐색을 선택하셨습니다. 어떤 분야의 채용 공고를 찾으시나요?\n1. IT/개발\n2. 경영/사무\n3. 영업/마케팅",
      2: "자기소개서 작성을 선택하셨습니다. 어떤 도움이 필요하신가요?\n1. 자기소개서 템플릿\n2. 맞춤형 작성 가이드\n3. 첨삭 서비스",
      3: "면접 연습을 선택하셨습니다. 어떤 유형의 면접 준비를 하시겠습니까?\n1. 기술 면접\n2. 인성 면접\n3. PT 면접",
    };
    for (const [key, value] of Object.entries(keywords)) {
      if (userInput.includes(key)) {
        return value;
      }
    }
    return "죄송합니다. 1, 2, 3 중에서 선택해주시거나, 구체적인 질문을 해주세요.";
  };

  // Sends a text message to the backend API and displays the responses
  const sendMessage = async () => {
    if (!input.trim()) return;
    const userInput = input;
    displayUserMessage(userInput);
    setInput("");
    setIsLoading(true);
    try {
      const response = await fetch("http://127.0.0.1:8000/api/chat/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ user_input: userInput }),
      });
      if (!response.ok) {
        const localResponse = generateBotResponse(userInput);
        displayBotMessage(localResponse);
        return;
      }
      const data = await response.json();
      if (!data?.message) {
        const localResponse = generateBotResponse(userInput);
        displayBotMessage(localResponse);
        return;
      }
      displayBotMessage(data.message);
    } catch (error) {
      console.error("API 요청 중 오류 발생:", error);
      const localResponse = generateBotResponse(userInput);
      displayBotMessage(localResponse);
    } finally {
      setIsLoading(false);
    }
  };

  // ===== 음성 녹음 및 STT (Whisper API) 관련 함수 =====

  // 녹음을 시작하는 함수
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      const chunks = [];
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };
      mediaRecorder.onstop = () => {
        const audio = new Blob(chunks, { type: "audio/webm" });
        setAudioBlob(audio);
        // 녹음이 종료되면 사용자가 별도 버튼을 눌러 STT 요청을 할 수 있습니다.
      };
      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error("마이크 접근 오류:", error);
    }
  };

  // 녹음을 중지하는 함수
  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // 녹음된 오디오를 OpenAI Whisper API로 전송하는 함수
  const sendAudioToOpenAI = async () => {
    if (!audioBlob) {
      alert("녹음된 음성이 없습니다.");
      return;
    }
    setIsTranscribing(true);
    setTranscription("");
    const formData = new FormData();
    formData.append("file", audioBlob, "audio.webm");
    formData.append("model", "whisper-1");
    formData.append("language", "ko");
    try {
      // OpenAI의 STT API 호출 (API 키는 안전하게 관리하세요)
      const response = await axios.post(
        "https://api.openai.com/v1/audio/transcriptions",
        formData,
        {
          headers: {
            Authorization: `Bearer ${process.env.REACT_APP_OPENAI_API_KEY}`,
            "Content-Type": "multipart/form-data",
          },
        }
      );
      const transcript = response.data.text;
      setTranscription(transcript);
      // 전사된 텍스트를 사용자 메시지로 추가하고, 챗봇 API로 전송
      displayUserMessage(transcript);
      const chatResponse = await fetch("http://127.0.0.1:8000/api/chat/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ user_input: transcript }),
      });
      if (chatResponse.ok) {
        const chatData = await chatResponse.json();
        displayBotMessage(chatData.message);
      } else {
        const localResponse = generateBotResponse(transcript);
        displayBotMessage(localResponse);
      }
    } catch (error) {
      console.error("STT API 오류:", error);
    } finally {
      setIsTranscribing(false);
    }
  };

  // =======================================================

  return (
    <div
      className="container-fluid p-0 vh-100 d-flex flex-column"
      style={{
        width: getResponsiveWidth(),
        margin: "0 auto",
        minWidth: "320px",
      }}
    >
      {/* 상단 바 */}
      <header
        className="d-flex align-items-center justify-content-between text-white px-3 py-2"
        style={{ backgroundColor: "#5e6aec", width: "100%" }}
      >
        <div className="d-flex align-items-center">
          <img
            src="/images/logo.png"
            alt="Company Logo"
            className="me-3"
            style={{ width: "150px", height: "60px" }}
          />
        </div>
        <div className="d-flex">
          <button
            className="btn btn-link text-white"
            onClick={() => navigate("/settings")}
            aria-label="Settings"
          >
            <FontAwesomeIcon icon={faCog} size="lg" />
          </button>
        </div>
      </header>

      {/* 챗봇 메시지 영역 */}
      <div className="flex-grow-1 p-3" style={{ width: "100%" }}>
        <div
          ref={scrollRef}
          className="chat-box p-4"
          style={{
            height: "calc(100vh - 200px)",
            width: "100%",
            overflowY: "auto",
            background: "#ffffff",
            border: "1px solid #dee2e6",
            borderRadius: "18px",
          }}
        >
          {messages.map((msg, index) => (
            <div
              key={`${msg.timestamp}-${index}`}
              className={`chat p-2 my-2 rounded d-flex align-items-start ${
                msg.sender === "user"
                  ? "custom-user-message text-white align-self-end"
                  : "custom-bot-message"
              }`}
              style={{
                maxWidth: "85%",
                borderRadius: "80px",
                position: "relative",
              }}
            >
              {msg.sender === "bot" && (
                <div className="bot-icon">
                  <FontAwesomeIcon icon={faUserCircle} />
                </div>
              )}
              <div className="chat-text">{msg.text}</div>
            </div>
          ))}
        </div>
        {isLoading && <ProgressBar />}

        {/* 전사된 텍스트 영역 */}
        {transcription && (
          <div
            style={{
              marginTop: "20px",
              padding: "10px",
              border: "1px solid #ccc",
              background: "#F9F9F9",
            }}
          >
            <strong>Transcription:</strong>
            <p>{transcription}</p>
          </div>
        )}

        {/* 입력창 영역 */}
        <div className="chat-input mt-3" style={{ width: "100%" }}>
          <div className="input-group" style={{ width: "100%" }}>
            <input
              type="text"
              className="form-control rounded-pill px-3"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              placeholder="메시지를 입력하세요."
              style={{
                borderRadius: "40px",
                paddingRight: "30px",
                width: "calc(100% - 60px)",
                marginRight: "10px",
              }}
            />
            <button
              className="send-btn"
              onClick={sendMessage}
              aria-label="Send message"
              style={{
                borderRadius: "50%",
                width: "45px",
                height: "45px",
                backgroundColor: "#5e6aec",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
              }}
            >
              <FontAwesomeIcon icon={faAngleRight} style={{ color: "white" }} />
            </button>
            {/* 음성 녹음 버튼 */}
            <button
              className="ms-2 btn btn-link"
              onClick={isRecording ? stopRecording : startRecording}
              aria-label="Voice Recording"
              style={{
                fontSize: "1.5rem",
                color: isRecording ? "red" : "#5e6aec",
              }}
            >
              <FontAwesomeIcon
                icon={isRecording ? faStopCircle : faMicrophone}
              />
            </button>
            {/* 녹음된 음성이 있을 경우, STT 요청 버튼 표시 */}
            {audioBlob && !isTranscribing && (
              <button
                className="ms-2 btn btn-link"
                onClick={sendAudioToOpenAI}
                aria-label="Send Audio"
                style={{
                  fontSize: "1.5rem",
                  color: "#5e6aec",
                }}
              >
                Send Audio
              </button>
            )}
            {isTranscribing && (
              <span className="ms-2" style={{ fontSize: "1rem" }}>
                Transcribing...
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chatbot;
