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
} from "@fortawesome/free-solid-svg-icons";

// Profile 컴포넌트는 로그인 정보를 표시하는 역할
import { Profile } from "./settings/Login";
import { DataTable } from "./settings/DataTable";

const Settings = () => {
  const [activeTab, setActiveTab] = useState("profile");
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userProfile, setUserProfile] = useState(null);
  const mainColor = "#5e6aec";
  const navigate = useNavigate();

  // 컴포넌트 마운트 시 localStorage에서 로그인 상태 및 사용자 정보 확인
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

  // 로그인 및 로그아웃 핸들러
  const handleLogin = () => navigate("/login"); // 로그인 페이지로 이동
  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("userProfile");
    setIsLoggedIn(false);
    setUserProfile(null);
  };

  // 예시용 데이터 (로그인 전에는 하드코딩된 정보)
  const resumes = [
    { id: 1, title: "네이버 자기소개서", date: "2024-02-06" },
    { id: 2, title: "카카오 자기소개서", date: "2024-02-05" },
  ];

  const interviews = [
    { id: 1, company: "네이버", date: "2024-02-06" },
    { id: 2, company: "카카오", date: "2024-02-05" },
  ];

  const jobPostings = [
    {
      id: 1,
      company: "네이버",
      position: "프론트엔드 개발자",
      date: "2024-02-06",
    },
    { id: 2, company: "카카오", position: "웹 개발자", date: "2024-02-05" },
  ];

  const renderContent = () => {
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
          <div className="bg-white p-4 rounded-3 shadow-sm">
            <h3 className="mb-4">작성된 자기소개서</h3>
            <DataTable
              headers={["제목", "작성일", "작업"]}
              data={resumes}
              renderActions={(resume) => (
                <>
                  <button className="btn btn-sm btn-outline-primary me-2">
                    보기
                  </button>
                  <button className="btn btn-sm btn-outline-danger">
                    삭제
                  </button>
                </>
              )}
            />
          </div>
        );
      case "interviews":
        return (
          <div className="bg-white p-4 rounded-3 shadow-sm">
            <h3 className="mb-4">면접 연습 내역</h3>
            <DataTable
              headers={["회사", "날짜", "작업"]}
              data={interviews}
              renderActions={(interview) => (
                <button className="btn btn-sm btn-outline-primary">
                  상세보기
                </button>
              )}
            />
          </div>
        );
      case "jobs":
        return (
          <div className="bg-white p-4 rounded-3 shadow-sm">
            <h3 className="mb-4">확인한 채용공고</h3>
            <DataTable
              headers={["회사", "포지션", "확인일", "작업"]}
              data={jobPostings}
              renderActions={(job) => (
                <button className="btn btn-sm btn-outline-primary">
                  공고 보기
                </button>
              )}
            />
          </div>
        );
      default:
        return null;
    }
  };

  const Sidebar = () => {
    const menuItems = [
      { id: "profile", icon: faUser, text: "내 정보" },
      { id: "resumes", icon: faFileAlt, text: "작성된 자기소개서" },
      { id: "interviews", icon: faComments, text: "면접 연습 내역" },
      { id: "jobs", icon: faBriefcase, text: "확인한 채용공고" },
    ];

    return (
      <div className="list-group w-100">
        {menuItems.map((item) => (
          <button
            key={item.id}
            className={`list-group-item list-group-item-action ${
              activeTab === item.id ? "active" : ""
            }`}
            onClick={() => setActiveTab(item.id)}
            style={{
              backgroundColor: activeTab === item.id ? mainColor : "",
              color: activeTab === item.id ? "white" : "",
              borderColor: activeTab === item.id ? mainColor : "",
            }}
            disabled={item.id !== "profile" && !isLoggedIn}
          >
            <FontAwesomeIcon icon={item.icon} className="me-2" />
            {item.text}
          </button>
        ))}
      </div>
    );
  };

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
            onClick={() => navigate("/")}
            style={{ width: "150px", height: "60px" }}
          />
        </div>
        <button
          className="btn text-white border border-white rounded-pill px-4 py-2"
          onClick={() => navigate("/chatbot")}
          style={{
            transition: "background-color 0.3s, color 0.3s",
          }}
          onMouseEnter={(e) => {
            e.target.style.backgroundColor = "white";
            e.target.style.color = mainColor; // 글씨 색
          }}
          onMouseLeave={(e) => {
            e.target.style.backgroundColor = "";
            e.target.style.color = "white";
          }}
        >
          챗봇
        </button>
      </header>
    );
  };

  return (
    <div
      className="container-fluid"
      style={{
        backgroundColor: "#ffffff",
        fontFamily: "'Noto Sans', sans-serif",
        minHeight: "90vh",
        width: "100vw",
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
              {renderContent()}
            </div>
          </div>
        </div>
        {/* Footer */}
        <footer className="bg-light py-4 w-100">
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
    </div>
  );
};

export default Settings;
