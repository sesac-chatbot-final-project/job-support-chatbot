import React, { useState, useEffect, useRef, useCallback } from "react";
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
  faPaperPlane,
  faVolumeUp,
  faVolumeMute,
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

// Custom hook for textarea auto-resize
const useAutoResize = (value) => {
  const textareaRef = useRef(null);
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      const newHeight = Math.min(textareaRef.current.scrollHeight, 150);
      textareaRef.current.style.height = `${newHeight}px`;
    }
  }, [value]);
  return textareaRef;
};

const ProgressBar = ({ progress = 0 }) => (
  <div className="mt-2 flex justify-center items-center w-full">
    <div className="w-1/2 max-w-xl">
      <div
        className="progress bg-gray-200"
        style={{
          height: "9px",
          borderRadius: "4px",
          width: "100%",
          position: "relative",
        }}
      >
        <div
          className="progress-bar"
          role="progressbar"
          style={{
            width: `${progress}%`,
            height: "100%",
            borderRadius: "4px",
            background:
              "linear-gradient(90deg, rgb(150, 159, 255) 0%, #8e96f3 100%)",
            transition: "width 0.3s ease-in-out",
          }}
          aria-valuenow={progress}
          aria-valuemin="0"
          aria-valuemax="100"
        />
      </div>
    </div>
  </div>
);

const urlRegex = /(https?:\/\/[^\s]+)/g;

// SpeechSynthesis API를 사용하여 텍스트를 음성으로 읽어주는 함수
const speakText = (text) => {
  if ("speechSynthesis" in window) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "ko-KR"; // 한국어 설정
    utterance.rate = 1;
    utterance.volume = 1;
    window.speechSynthesis.cancel(); // 이전 재생 취소
    window.speechSynthesis.speak(utterance);
  } else {
    console.error("SpeechSynthesis API is not supported in this browser.");
  }
};

const Chatbot = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);
  // ttsUrl는 자동 재생 실패 시 수동 재생용으로 사용 (참고용)
  const [ttsUrl, setTtsUrl] = useState(null);
  // 기본 TTS 설정을 "꺼진" 상태로 설정 (false)
  const [ttsEnabled, setTtsEnabled] = useState(false);
  const navigate = useNavigate();
  const scrollRef = useAutoScroll(messages);
  const [progress, setProgress] = useState(0);
  const [chatBoxHeight, setChatBoxHeight] = useState("calc(100vh - 200px)");
  const textareaRef = useAutoResize(input);

  // 음성 녹음 관련 상태 및 refs (기존 기능 유지)
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const didInit = useRef(false);

  const updateChatBoxHeight = useCallback(() => {
    if (scrollRef.current) {
      const contentHeight = scrollRef.current.scrollHeight;
      const windowHeight = window.innerHeight;
      const minHeight = windowHeight - 200;
      const newHeight = Math.max(minHeight, contentHeight);
      setChatBoxHeight(`${newHeight}px`);
    }
  }, [scrollRef]);

  useEffect(() => {
    updateChatBoxHeight();
  }, [messages, updateChatBoxHeight]);

  const processMessage = useCallback((text) => {
    if (typeof text !== "string") return text;
    return text.split("\n").map((line, lineIndex) => {
      const parts = line.split(urlRegex);
      return (
        <React.Fragment key={lineIndex}>
          {parts.map((part, partIndex) => {
            if (part.match(urlRegex)) {
              return (
                <a
                  key={partIndex}
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
          })}
          {lineIndex < text.split("\n").length - 1 && <br />}
        </React.Fragment>
      );
    });
  }, []);

  const displayBotMessage = useCallback(
    (message) => {
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
      // TTS가 활성화된 경우에만 자동 음성 재생 시도
      if (ttsEnabled && message.includes("면접")) {
        speakText(message);
      }
    },
    [processMessage, ttsEnabled]
  );

  const displayUserMessage = useCallback(
    (message) => {
      if (!message?.trim()) return;
      setMessages((prev) => [
        ...prev,
        {
          sender: "user",
          text: processMessage(message),
          timestamp: new Date().toISOString(),
        },
      ]);
    },
    [processMessage]
  );

  // 수동 음성 재생 버튼에서 사용할 playTTS 함수 정의
  const playTTS = useCallback(() => {
    if (ttsUrl) {
      const audio = new Audio(ttsUrl);
      audio.volume = 1;
      audio
        .play()
        .catch((err) => console.error("Manual audio playback failed:", err));
    }
  }, [ttsUrl]);

  useEffect(() => {
    if (!didInit.current) {
      didInit.current = true;
      displayBotMessage(
        "안녕하세요, 취업 지원 서비스 챗봇입니다! 채용 공고, 자기소개서 초안 작성, 모의 면접 기능이 있습니다. 무엇을 도와드릴까요?"
      );
    }
  }, [displayBotMessage]);

  useEffect(() => {
    const handleResize = () => {
      setWindowWidth(window.innerWidth);
      updateChatBoxHeight();
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [updateChatBoxHeight]);

  const getResponsiveWidth = useCallback(() => {
    return `${Math.min(windowWidth, 1900)}px`;
  }, [windowWidth]);

  const sendMessage = useCallback(async () => {
    if (!input.trim()) return;
    const token = localStorage.getItem("token");
    if (!token) {
      displayBotMessage("로그인 후 사용해 주세요.");
      return;
    }
    const userInput = input;
    displayUserMessage(userInput);
    setInput("");
    setIsLoading(true);
    setProgress(0);
    setTtsUrl(null);
    const controller = new AbortController();
    const progressInterval = setInterval(() => {
      setProgress((prev) => (prev >= 90 ? 90 : prev + 10));
    }, 300);
    try {
      const response = await fetch("http://127.0.0.1:8000/api/chat/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ user_input: userInput }),
        signal: controller.signal,
      });
      if (!response.ok) throw new Error("API request failed");
      const data = await response.json();
      displayBotMessage(data.message || "죄송합니다. 응답을 받지 못했습니다.");
      // SpeechSynthesis API는 displayBotMessage 내에서 자동 호출됨.
    } catch (error) {
      if (error.name === "AbortError") {
        displayBotMessage("요청이 취소되었습니다.");
      } else {
        console.error("API 요청 중 오류 발생:", error);
        displayBotMessage("죄송합니다. 서버와의 통신 중 오류가 발생했습니다.");
      }
    } finally {
      clearInterval(progressInterval);
      setProgress(100);
      setTimeout(() => {
        setIsLoading(false);
        setProgress(0);
      }, 500);
    }
    return () => {
      controller.abort();
      clearInterval(progressInterval);
    };
  }, [input, displayUserMessage, displayBotMessage]);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };
      mediaRecorder.onstop = () => {
        const audio = new Blob(chunksRef.current, { type: "audio/webm" });
        setAudioBlob(audio);
        stream.getTracks().forEach((track) => track.stop());
      };
      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error("마이크 접근 오류:", error);
      alert("마이크 접근에 실패했습니다. 마이크 권한을 확인해주세요.");
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state === "recording"
    ) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  }, []);

  const sendAudioToOpenAI = useCallback(async () => {
    if (!audioBlob) {
      alert("녹음된 음성이 없습니다.");
      return;
    }
    const token = localStorage.getItem("token");
    if (!token) {
      displayBotMessage("로그인 후 사용해 주세요.");
      return;
    }
    setIsTranscribing(true);
    const formData = new FormData();
    formData.append("file", audioBlob, "audio.webm");
    formData.append("model", "whisper-1");
    formData.append("language", "ko");
    try {
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
      displayUserMessage(transcript);
      const chatResponse = await fetch("http://127.0.0.1:8000/api/chat/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ user_input: transcript }),
      });
      if (chatResponse.ok) {
        const chatData = await chatResponse.json();
        displayBotMessage(chatData.message);
        if (chatData.message && ttsEnabled) {
          speakText(chatData.message);
        }
      } else {
        throw new Error("Chat API request failed");
      }
    } catch (error) {
      console.error("STT API 오류:", error);
      displayBotMessage("음성 처리 중 오류가 발생했습니다.");
    } finally {
      setIsTranscribing(false);
      setAudioBlob(null);
    }
  }, [audioBlob, displayUserMessage, displayBotMessage, ttsEnabled]);

  return (
    <div
      className="container-fluid p-0 vh-100 d-flex flex-column"
      style={{
        width: getResponsiveWidth(),
        margin: "0 auto",
        minWidth: "320px",
      }}
    >
      <header
        className="d-flex align-items-center justify-content-between text-white px-3 py-2"
        style={{
          backgroundColor: "#5e6aec",
          width: "100%",
          flexShrink: 0,
        }}
      >
        <div className="d-flex align-items-center">
          <img
            src="/images/logo.png"
            alt="Company Logo"
            className="me-3"
            style={{ width: "150px", height: "60px" }}
          />
        </div>
        <div className="d-flex align-items-center">
          {/* TTS On/Off 토글 버튼 */}
          <button
            className="btn btn-link text-white"
            onClick={() => setTtsEnabled((prev) => !prev)}
            aria-label="Toggle TTS"
            title="TTS 토글"
          >
            <FontAwesomeIcon
              icon={ttsEnabled ? faVolumeUp : faVolumeMute}
              size="lg"
            />
          </button>
          <button
            className="btn btn-link text-white"
            onClick={() => navigate("/settings")}
            aria-label="Settings"
          >
            <FontAwesomeIcon icon={faCog} size="lg" />
          </button>
        </div>
      </header>
      <div
        className="d-flex flex-column flex-grow-1 p-4"
        style={{ width: "100%" }}
      >
        <div
          ref={scrollRef}
          className="chat-box p-4"
          style={{
            height: chatBoxHeight,
            width: "100%",
            overflowY: "auto",
            background: "#ffffff",
            border: "1px solid #dee2e6",
            borderRadius: "18px",
            transition: "height 0.3s ease-in-out",
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
                maxWidth: "80%",
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
        {isLoading && <ProgressBar progress={progress} />}
        {/* 수동 음성 재생 버튼 (ttsUrl이 있을 경우) */}
        {ttsUrl && (
          <div style={{ textAlign: "center", marginTop: "10px" }}>
            <button className="btn btn-primary" onClick={playTTS}>
              음성 재생
            </button>
          </div>
        )}
        <div className="chat-input mt-3" style={{ width: "100%" }}>
          <div className="input-group" style={{ width: "100%" }}>
            <textarea
              ref={textareaRef}
              className="form-control px-4 custom-scrollbar"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage();
                }
              }}
              placeholder="메시지를 입력하세요."
              rows="1"
              style={{
                borderRadius: "25px",
                paddingRight: "30px",
                resize: "none",
                minHeight: "40px",
                maxHeight: "150px",
                maxWidth: "95%",
                overflowY: "hidden",
                lineHeight: "1.5",
                paddingTop: "8px",
                paddingBottom: "8px",
              }}
              onInput={(e) => {
                if (e.target.scrollHeight > 40) {
                  e.target.style.overflowY = "auto";
                } else {
                  e.target.style.overflowY = "hidden";
                }
              }}
            />
            <div
              className="input-group-append d-flex align-items-center"
              style={{ marginLeft: "10px" }}
            >
              <button
                className="btn btn-link"
                onClick={isRecording ? stopRecording : startRecording}
                aria-label="Voice Recording"
                style={{
                  fontSize: "1.5rem",
                  color: isRecording ? "red" : "#5e6aec",
                  padding: "0 8px",
                }}
              >
                <FontAwesomeIcon
                  icon={isRecording ? faStopCircle : faMicrophone}
                />
              </button>
              {audioBlob && !isTranscribing && (
                <button
                  className="btn btn-link"
                  onClick={sendAudioToOpenAI}
                  aria-label="Send Audio"
                  style={{
                    fontSize: "1.5rem",
                    color: "#5e6aec",
                    padding: "0 8px",
                  }}
                >
                  <FontAwesomeIcon icon={faPaperPlane} />
                </button>
              )}
              <button
                className="send-btn"
                onClick={sendMessage}
                aria-label="Send message"
                style={{
                  borderRadius: "50%",
                  width: "40px",
                  height: "40px",
                  backgroundColor: "#5e6aec",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                }}
              >
                <FontAwesomeIcon
                  icon={faAngleRight}
                  style={{ color: "white", fontSize: "1.3rem" }}
                />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chatbot;
