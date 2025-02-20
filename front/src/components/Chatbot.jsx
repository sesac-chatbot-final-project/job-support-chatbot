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
import RingLoader from "react-spinners/RingLoader";

// 전체 화면 로딩 오버레이 컴포넌트
const LoadingOverlay = ({ loading }) => {
  if (!loading) return null;
  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        backgroundColor: "rgba(223, 223, 223, 0.3)",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        zIndex: 1000,
      }}
    >
      <RingLoader color="#5e6aec" loading={loading} size={100} />
    </div>
  );
};

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

// URL 감지를 위한 정규표현식
const urlRegex = /(https?:\/\/[^\s]+)/g;

// SpeechSynthesis API를 사용하여 텍스트를 음성으로 읽어주는 함수
const speakText = (text) => {
  if ("speechSynthesis" in window) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "ko-KR";
    utterance.rate = 1;
    utterance.volume = 1;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  } else {
    console.error("SpeechSynthesis API is not supported in this browser.");
  }
};

const Chatbot = () => {
  // 상태들
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [ttsUrl, setTtsUrl] = useState(null);
  // 기본 TTS는 꺼진 상태
  const [ttsEnabled, setTtsEnabled] = useState(false);
  // 추가: 답변 스트리밍 상태 (답변 생성 완료 전까지 새로운 입력을 막기 위함)
  const [isStreaming, setIsStreaming] = useState(false);
  // 녹음 상태
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  // UI 레이아웃 관련
  const scrollRef = useAutoScroll(messages);
  const textareaRef = useAutoResize(input);

  const navigate = useNavigate();
  const didInit = useRef(false);

  // 메시지 내 줄바꿈 및 링크 처리
  const processMessage = useCallback((text) => {
    if (typeof text !== "string") return text;
    return text.split("\n").map((line, index) => {
      const parts = line.split(urlRegex);
      return (
        <React.Fragment key={index}>
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
          {index < text.split("\n").length - 1 && <br />}
        </React.Fragment>
      );
    });
  }, []);

  // 긴 메시지 스트리밍
  const simulateStreaming = useCallback(
    (fullText) => {
      const words = fullText.split(" ");
      let partialText = "";
      setIsStreaming(true);
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "", timestamp: new Date().toISOString() },
      ]);
      words.forEach((word, index) => {
        setTimeout(() => {
          partialText += word + " ";
          setMessages((prev) => {
            const newMessages = [...prev];
            newMessages[newMessages.length - 1].text =
              processMessage(partialText);
            return newMessages;
          });
          if (index === words.length - 1) {
            // 스트리밍 완료
            setIsStreaming(false);
          }
        }, index * 100);
      });
    },
    [processMessage]
  );

  // 봇 메시지 표시
  const displayBotMessage = useCallback(
    (message) => {
      if (message.length > 100) {
        simulateStreaming(message);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            sender: "bot",
            text: processMessage(message),
            timestamp: new Date().toISOString(),
          },
        ]);
        // 짧은 메시지면 스트리밍 상태를 false로 보장
        setIsStreaming(false);
      }
      if (ttsEnabled && message.includes("면접")) {
        speakText(message);
      }
    },
    [processMessage, ttsEnabled, simulateStreaming]
  );

  // 사용자 메시지 표시
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

  // TTS 수동 재생
  const playTTS = useCallback(() => {
    if (ttsUrl) {
      const audio = new Audio(ttsUrl);
      audio.volume = 1;
      audio
        .play()
        .catch((err) => console.error("Manual audio playback failed:", err));
    }
  }, [ttsUrl]);

  // 초기 웰컴 메시지
  useEffect(() => {
    if (!didInit.current) {
      didInit.current = true;
      displayBotMessage(
        "안녕하세요, 취업 지원 서비스 챗봇입니다! \n\
        채용 공고 제공, 자기소개서 초안 작성, 모의 면접 기능이 있습니다.\n\n\
        ℹ️ 채용 공고 제공을 원하시면 직무 이름과 함께 공고를 요청해주세요. \n\
            🌟 Java 등 기술 이름을 영어로 입력하시는 것을 추천드립니다! (예: Java 개발자 공고 알려줘) \n\n\
        🧾 자기소개서 초안 작성을 원하시면 자기소개서 작성을 요청해주세요. \n\
            🌟 특정 채용 공고를 참고하여 작성을 원하시면, 채용 공고를 탐색한 이후에 기능을 이용해주세요. \n\n\
        🗨️ 모의 면접의 경우 인성 면접과 기술 면접으로 나누어져 있으며, 기술 면접의 경우 자기소개서 작성 이후 이용하실 수 있습니다.\n\n\
        무엇을 도와드릴까요?"
      );
    }
  }, [displayBotMessage]);

  // 입력창 자동 포커스: 답변 생성이 완료되면 포커스
  useEffect(() => {
    if (!isLoading && !isStreaming && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [isLoading, isStreaming, textareaRef]);

  // 메시지 전송 함수
  const sendMessage = useCallback(async () => {
    // 답변 생성 중이면 새 메시지 전송 방지
    if (isLoading || isStreaming) return;
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
    setTtsUrl(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/api/chat/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ user_input: userInput }),
      });
      if (!response.ok) throw new Error("API request failed");
      const data = await response.json();
      displayBotMessage(data.message || "죄송합니다. 응답을 받지 못했습니다.");
    } catch (error) {
      if (error.name === "AbortError") {
        displayBotMessage("요청이 취소되었습니다.");
      } else {
        console.error("API 요청 중 오류 발생:", error);
        displayBotMessage("죄송합니다. 서버와의 통신 중 오류가 발생했습니다.");
      }
    } finally {
      setIsLoading(false);
    }
  }, [input, displayUserMessage, displayBotMessage, isLoading, isStreaming]);

  // 녹음 시작
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

  // 녹음 중지
  const stopRecording = useCallback(() => {
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state === "recording"
    ) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  }, []);

  // 녹음 파일 전송
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
      className="container-fluid"
      style={{
        height: "99vh",
        overflow: "visible",
        display: "flex",
        flexDirection: "column",
        width: "101vw",
        maxWidth: "none",
      }}
    >
      <header
        className="d-flex justify-content-between px-3 px-md-5 py-3 container-fluid"
        style={{
          backgroundColor: "#5e6aec",
          flexShrink: 0,
          width: "100vw",
        }}
      >
        <div className="d-flex align-items-start">
          <img
            src="/images/logo.png"
            alt="Company Logo"
            className="me-3"
            onClick={() => navigate("/")}
            style={{ width: "150px", height: "60px", cursor: "pointer" }}
          />
        </div>
        <div className="d-flex align-items-center">
          {/* TTS 토글 버튼 */}
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
        style={{
          flexGrow: 1,
          overflowY: "auto",
          padding: "1rem",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div
          ref={scrollRef}
          className="chat-box"
          style={{
            flexGrow: 1,
            overflowY: "auto",
            background: "#ffffff",
            border: "1px solid #dee2e6",
            borderRadius: "32px",
            padding: "1rem",
          }}
        >
          {messages.map((msg, index) => (
            <div
              key={`${msg.timestamp}-${index}`}
              className={`chat p-2 my-3 mx-5 d-flex align-items-start ${
                msg.sender === "user"
                  ? "custom-user-message text-white align-self-end"
                  : "custom-bot-message"
              }`}
              style={{
                maxWidth: "80%",
                borderRadius: "18px",
                position: "relative",
                paddingLeft: "16px",
                paddingRight: "16px",
              }}
            >
              {msg.sender === "bot" && (
                <div className="bot-icon">
                  <FontAwesomeIcon icon={faUserCircle} />
                </div>
              )}
              <div
                className="chat-text p-1 px-2"
                style={{ fontSize: "1.05rem", fontWeight: 500 }}
              >
                {msg.text}
              </div>
            </div>
          ))}
        </div>

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
                  if (!isLoading && !isStreaming) {
                    sendMessage();
                  }
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
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
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
                disabled={isLoading || isStreaming}
                aria-label="Send message"
                style={{
                  borderRadius: "50%",
                  width: "40px",
                  height: "40px",
                  backgroundColor:
                    isLoading || isStreaming ? "#ccc" : "#5e6aec",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                  border: "none",
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
      {/* 전체 화면 로딩 오버레이: 이제 isLoading 상태에만 의존 */}
      <LoadingOverlay loading={isLoading} />
    </div>
  );
};

export default Chatbot;
