import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "bootstrap/dist/css/bootstrap.min.css";
import "../styles.css";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faAngleRight,
  faUserCircle,
  faCog,
} from "@fortawesome/free-solid-svg-icons";

const Chatbot = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);
  const navigate = useNavigate();

  useEffect(() => {
    const handleResize = () => {
      setWindowWidth(window.innerWidth);
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  useEffect(() => {
    const initialMessages = [
      "안녕하세요! 저는 취업 지원 서비스 챗봇입니다. 원하는 서비스를 선택해주세요!",
      "1. 채용 공고 탐색\n2. 자기소개서 작성\n3. 면접 연습",
    ];

    initialMessages.forEach((msg, index) => {
      setTimeout(() => displayBotMessage(msg), index * 500); // 메시지 딜레이 추가
    });
  }, []);

  const getResponsiveWidth = () => {
    const width = Math.min(windowWidth * 1, 1900); // 최대 너비 1900px
    return `${width}px`;
  };

  const sendMessage = async () => {
    if (!input.trim()) return;

    // 사용자 메시지 표시
    displayUserMessage(input);

    // 로딩 메시지 추가
    displayBotMessage("응답을 기다리는 중...");

    try {
      // Django 서버 URL
      const API_URL = "http://127.0.0.1:8000/api/chat/";

      // API 호출
      const response = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ user_input: input }), // 입력값 전달
      });

      if (!response.ok) {
        throw new Error("서버 응답 실패");
      }

      const data = await response.json();

      // 봇 응답 표시
      displayBotMessage(data.message || "응답이 없습니다.");
    } catch (error) {
      console.error("API 요청 중 오류 발생:", error);
      displayBotMessage("서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.");
    } finally {
      setInput(""); // 입력창 초기화
    }
  };

  const displayUserMessage = (message) => {
    setMessages((prevMessages) => [
      ...prevMessages,
      {
        sender: "user",
        text: message.split("\n").map((line, index) => (
          <React.Fragment key={index}>
            {line}
            <br />
          </React.Fragment>
        )),
      },
    ]);
  };

  const displayBotMessage = (message) => {
    setMessages((prevMessages) => [
      ...prevMessages,
      {
        sender: "bot",
        text: message.split("\n").map((line, index) => (
          <React.Fragment key={index}>
            {line}
            <br />
          </React.Fragment>
        )),
      },
    ]);
  };

  const containerStyle = {
    width: getResponsiveWidth(),
    margin: "0 auto",
    minWidth: "320px", // 최소 너비 설정
  };

  return (
    <div
      className="container-fluid p-0 vh-100 d-flex flex-column"
      style={containerStyle}
    >
      {/* 상단 바 */}
      <header
        className="d-flex align-items-center justify-content-between text-white px-3 py-2"
        style={{
          backgroundColor: "#5e6aec",
          width: "100%",
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

        <div className="d-flex">
          <button
            className="btn btn-link text-white"
            onClick={() => navigate("/settings")}
          >
            <FontAwesomeIcon icon={faCog} size="lg" />
          </button>
        </div>
      </header>

      {/* 챗봇 UI */}
      <div className="flex-grow-1 p-3" style={{ width: "100%" }}>
        <div
          id="chatBox"
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
              key={index}
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

        {/* 입력창 */}
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
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chatbot;
