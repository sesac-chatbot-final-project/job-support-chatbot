import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "../styles.css";
import "bootstrap/dist/css/bootstrap.min.css";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faUser,
  faFileAlt,
  faComments,
  faBriefcase,
  faAngleRight,
} from "@fortawesome/free-solid-svg-icons";

// Profile 컴포넌트는 로그인 정보를 표시하는 역할
import { Profile } from "./settings/Login";
import ResumeModal from "./ResumeModal";

const Settings = () => {
  const [activeTab, setActiveTab] = useState("profile");
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userProfile, setUserProfile] = useState(null);

  // 백엔드에서 받아온 데이터
  const [resumes, setResumes] = useState([]);
  const [interviews, setInterviews] = useState([]);
  const [jobPostings, setJobPostings] = useState([]);

  // 모달에서 표시할 자기소개서
  const [selectedResume, setSelectedResume] = useState(null);

  const mainColor = "#5e6aec";
  const navigate = useNavigate();

  // (1) 로그인 상태 확인
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      setIsLoggedIn(true);
      const storedProfile = localStorage.getItem("userProfile");
      if (storedProfile) {
        setUserProfile(JSON.parse(storedProfile));
      }
    }
  }, []);

  // (2) 로그인된 경우, 백엔드 API를 통해 데이터 불러오기
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (isLoggedIn && token) {
      // 자기소개서 목록
      fetch("http://127.0.0.1:8000/api/resumes/", {
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      })
        .then((res) => res.json())
        .then((data) => setResumes(data))
        .catch((err) => console.error("Resumes API 에러:", err));

      // 면접 연습 내역
      fetch("http://127.0.0.1:8000/api/interviews/", {
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      })
        .then((res) => res.json())
        .then((data) => setInterviews(data))
        .catch((err) => console.error("Interviews API 에러:", err));

      // 확인한 채용공고 목록
      fetch("http://127.0.0.1:8000/api/job-postings/", {
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      })
        .then((res) => res.json())
        .then((data) => setJobPostings(data))
        .catch((err) => console.error("Job Postings API 에러:", err));
    }
  }, [isLoggedIn]);

  // 로그인 / 로그아웃 핸들러
  const handleLogin = () => navigate("/login");
  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("userProfile");
    setIsLoggedIn(false);
    setUserProfile(null);
    setResumes([]);
    setInterviews([]);
    setJobPostings([]);
  };

  // 자소서 "보기" 버튼 -> 모달 오픈
  const viewResume = (resume) => {
    setSelectedResume(resume);
  };

  // 모달 닫기
  const closeModal = () => {
    setSelectedResume(null);
  };

  // "작성된 자기소개서" 탭: 제목, 작성일, "보기" 버튼 (자소서 내용은 모달에서만 표시)
  const renderResumesTable = () => {
    return (
      <table className="table">
        <thead>
          <tr>
            <th>제목</th>
            <th style={{ width: "200px" }}>작성일</th>
          </tr>
        </thead>
        <tbody>
          {resumes.map((item) => (
            <tr key={item.id}>
              <td>{item.title}</td>
              <td>
                {item.date}{" "}
                <button
                  className="btn btn-sm ms-3 px-4 rounded-5"
                  style={{ backgroundColor: "#5e6aec", color: "white" }}
                  onClick={() => viewResume(item)}
                >
                  보기
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  };

  // "면접 연습 내역" 탭
  const renderInterviewsTable = () => {
    return (
      <table className="table">
        <thead>
          <tr>
            <th>질문</th>
            <th>날짜</th>
          </tr>
        </thead>
        <tbody>
          {interviews.map((item) => (
            <tr key={item.id}>
              <td>{item.question}</td>
              <td>{item.date}</td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  };

  // "확인한 채용공고" 탭: 제목, 회사명, 날짜, 그리고 "바로가기" 버튼
  const renderJobsTable = () => {
    return (
      <table className="table">
        <thead>
          <tr>
            <th>제목</th>
            <th>회사명</th>
            <th>날짜</th>
            <th style={{ width: "160px", height: "26px" }}>링크</th>
          </tr>
        </thead>
        <tbody>
          {jobPostings.map((item) => (
            <tr key={item.id}>
              <td>{item.제목}</td>
              <td>{item.회사명}</td>
              <td>{item.date}</td>
              <td>
                <button
                  className="btn btn-sm rounded-5"
                  style={{ backgroundColor: "#5e6aec", color: "white" }}
                  onClick={() => {
                    if (item.link) {
                      window.open(item.link, "_blank");
                    } else {
                      alert("링크 정보가 없습니다.");
                    }
                  }}
                >
                  바로가기
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  };

  // 사이드바 컴포넌트
  const Sidebar = () => {
    const menuItems = [
      { id: "profile", icon: faUser, text: "내 정보" },
      { id: "resumes", icon: faFileAlt, text: "작성된 자기소개서" },
      { id: "interviews", icon: faComments, text: "면접 연습 내역" },
      { id: "jobs", icon: faBriefcase, text: "확인한 채용공고" },
    ];

    return (
      <div
        className="d-flex justify-content-center align-items-center flex-grow-1 py-2"
        style={{
          width: "100%",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "100%",
          marginLeft: "10%", // 오른쪽으로 이동
        }}
      >
        <div
          className="list-group shadow-sm"
          style={{
            display: "flex",
            flexDirection: "column",
            width: "clamp(500px, 90vw, 1200px)", // 너비 확장
            backgroundColor: "#ffffff",
            borderRadius: "20px",
            overflow: "hidden",
            boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)",
            padding: "8px",
          }}
        >
          {menuItems.map((item) => (
            <button
              key={item.id}
              className="list-group-item list-group-item-action d-flex align-items-center justify-content-between"
              onClick={() => setActiveTab(item.id)}
              style={{
                backgroundColor:
                  activeTab === item.id ? mainColor : "transparent",
                color: activeTab === item.id ? "white" : "#333",
                borderColor: "transparent",
                fontSize: "1.1rem",
                fontWeight: "540",
                padding: "16px 20px",
                borderRadius: "20px",
                marginBottom: "8px",
                transition: "all 0.3s ease-in-out",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                width: "100%",
              }}
              disabled={item.id !== "profile" && !isLoggedIn}
              onMouseEnter={(e) => {
                if (activeTab !== item.id) {
                  e.target.style.backgroundColor = "#f5f5f5";
                }
              }}
              onMouseLeave={(e) => {
                if (activeTab !== item.id) {
                  e.target.style.backgroundColor = "transparent";
                }
              }}
            >
              <div className="d-flex align-items-center">
                <FontAwesomeIcon
                  icon={item.icon}
                  className="me-3"
                  style={{
                    fontSize: "1.3rem",
                    color: activeTab === item.id ? "white" : "#555",
                  }}
                />
                {item.text}
              </div>
              <FontAwesomeIcon
                icon={faAngleRight}
                style={{
                  fontSize: "1.25rem",
                  color: activeTab === item.id ? "white" : "#afafaf",
                }}
              />
            </button>
          ))}
        </div>
      </div>
    );
  };

  // 헤더 컴포넌트
  const Header = () => {
    return (
      <header
        className="d-flex justify-content-between align-items-center px-3 px-md-5 py-3 container-fluid"
        style={{
          backgroundColor: mainColor,
          width: "100vw",
          maxWidth: "none",
        }}
      >
        <div className="d-flex align-items-center">
          <img
            src="/images/logo.png"
            alt="Company Logo"
            className="me-3"
            onClick={() => navigate("/", { replace: true })}
            style={{ width: "150px", height: "60px", cursor: "pointer" }}
          />
        </div>
        <div className="d-flex align-items-center gap-2">
          {isLoggedIn ? (
            <>
              <button
                className="btn text-white border border-white rounded-pill px-4 py-2"
                onClick={() => navigate("/chatbot")}
                style={{
                  transition: "background-color 0.3s, color 0.3s",
                }}
                onMouseEnter={(e) => {
                  e.target.style.backgroundColor = "white";
                  e.target.style.color = mainColor;
                }}
                onMouseLeave={(e) => {
                  e.target.style.backgroundColor = "";
                  e.target.style.color = "white";
                }}
              >
                챗봇
              </button>
              <button
                className="btn btn-light rounded-pill px-4 py-2"
                onClick={handleLogout}
                style={{ color: mainColor }}
              >
                로그아웃
              </button>
            </>
          ) : (
            <button
              className="btn btn-outline-light rounded-pill px-4 py-2"
              onClick={handleLogin}
            >
              로그인
            </button>
          )}
        </div>
      </header>
    );
  };

  return (
    <div
      className="d-flex flex-column min-vh-100"
      style={{
        backgroundColor: "#ffffff",
        fontFamily: "'Noto Sans', sans-serif",
        minHeight: "90vh",
        maxHeight: "100vh",
        width: "101vw",
        maxWidth: "none",
      }}
    >
      <div
        style={{
          width: "100vw",
          maxWidth: "none",
          display: "flex",
          flexDirection: "column",
          flex: 1,
        }}
      >
        <Header />
        <div className="flex-grow-1 d-flex justify-content-center">
          <div
            className="row mt-4"
            style={{ width: "100%", margin: 0, flex: 1 }}
          >
            <div
              className="col-md-11 d-flex justify-content-center"
              style={{ padding: "0 20px" }}
            >
              <Sidebar />
            </div>
            <div className="col-md-14" style={{ padding: "0 20px" }}>
              {(() => {
                switch (activeTab) {
                  case "profile":
                    return (
                      <Profile
                        isLoggedIn={isLoggedIn}
                        userProfile={isLoggedIn ? userProfile : null}
                        handleLogin={handleLogin}
                        handleLogout={handleLogout}
                        mainColor={mainColor}
                      />
                    );
                  case "resumes":
                    return (
                      <div className="bg-white p-5 rounded-3 shadow-sm">
                        <h3 className="mb-4 py-3">
                          <strong>작성된 자기소개서</strong>
                        </h3>
                        {renderResumesTable()}
                      </div>
                    );
                  case "interviews":
                    return (
                      <div className="bg-white p-4 rounded-3 shadow-sm">
                        <h3 className="mb-4 py-2">
                          <strong>면접 연습 내역</strong>
                        </h3>
                        {renderInterviewsTable()}
                      </div>
                    );
                  case "jobs":
                    return (
                      <div className="bg-white p-4 rounded-3 shadow-sm">
                        <h3 className="mb-4 py-2">
                          <strong>확인한 채용공고</strong>
                        </h3>
                        {renderJobsTable()}
                      </div>
                    );
                  default:
                    return null;
                }
              })()}
            </div>
          </div>
        </div>
        <footer className="bg-light py-4 mt-auto w-100">
          <div className="container d-flex justify-content-center gap-3">
            <button
              onClick={() => navigate("/customer-support")}
              className="btn btn-link text-secondary"
            >
              고객센터
            </button>
            <button
              onClick={() => navigate("/terms")}
              className="btn btn-link text-secondary"
            >
              이용약관
            </button>
          </div>
          <div className="text-center mt-3">
            <p className="text-muted" style={{ fontSize: "12px" }}>
              © 2024 jobara Company. All rights reserved.
            </p>
          </div>
        </footer>
      </div>

      {/* 모달: 선택된 자소서 내용 확인 */}
      {selectedResume && (
        <ResumeModal resume={selectedResume} onClose={closeModal} />
      )}
    </div>
  );
};

export default Settings;
