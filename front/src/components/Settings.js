import React, { useState } from "react";
import "../styles.css";
import "bootstrap/dist/css/bootstrap.min.css";
import { Header } from "./settings/Header";
import { Sidebar } from "./settings/Sidebar";
import { LoginPage } from "./settings/LoginPage";
import { Profile } from "./settings/Profile";
import { DataTable } from "./settings/DataTable";

const Settings = () => {
  const [activeTab, setActiveTab] = useState("profile");
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [showLoginPage, setShowLoginPage] = useState(false);
  const mainColor = "#5e6aec";
  const maxWidth = "1900px";

  // 로그인 및 로그아웃 핸들러 추가
  const handleLogin = () => setIsLoggedIn(true);
  const handleLogout = () => setIsLoggedIn(false);
  const handleSocialLogin = () => {
    setIsLoggedIn(true);
    setShowLoginPage(false);
  };

  const userProfile = {
    name: "박아롱",
    email: "arong@example.com",
    phone: "010-1234-5678",
    position: "프론트엔드 개발자",
    career: "신입",
  };

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
    if (showLoginPage) {
      return (
        <LoginPage
          handleSocialLogin={handleSocialLogin}
          mainColor={mainColor}
        />
      );
    }

    switch (activeTab) {
      case "profile":
        return (
          <Profile
            isLoggedIn={isLoggedIn}
            userProfile={userProfile}
            handleLogout={handleLogout}
            handleLogin={handleLogin}
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

  return (
    <div
      style={{
        backgroundColor: "#ffffff",
        fontFamily: "'Noto Sans', sans-serif",
        minHeight: "90vh",
        display: "flex",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: maxWidth,
          display: "flex",
          flexDirection: "column",
          flex: 1,
        }}
      >
        <Header mainColor={mainColor} />
        <div className="flex-grow-1 d-flex justify-content-center">
          <div
            className="row mt-4"
            style={{ width: "100%", margin: 0, flex: 1 }}
          >
            <div className="col-md-3" style={{ padding: "0 5px" }}>
              <Sidebar
                activeTab={activeTab}
                setActiveTab={setActiveTab}
                isLoggedIn={isLoggedIn}
                mainColor={mainColor}
              />
            </div>
            <div className="col-md-9" style={{ padding: "0 5px" }}>
              {renderContent()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
