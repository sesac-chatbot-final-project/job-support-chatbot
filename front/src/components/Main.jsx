import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "bootstrap/dist/css/bootstrap.min.css";

const Main = () => {
  const navigate = useNavigate();
  const mainColor = "#5e6aec";
  const grayColor = "#6c757d";

  // 로그인 상태를 관리할 state 추가
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  // 컴포넌트 마운트 시 localStorage에서 토큰이 있는지 확인
  useEffect(() => {
    setTimeout(() => {
      const token = localStorage.getItem("token");
      setIsLoggedIn(token !== null);
    }, 0); // 즉시 실행하되 렌더링 이후 적용
  }, []);

  // 로그아웃 핸들러
  const handleLogout = () => {
    localStorage.removeItem("token");
    // 필요한 경우 다른 로그인 관련 데이터도 제거 가능
    setIsLoggedIn(false);
    navigate("/"); // 로그아웃 후 홈으로 이동
  };

  const tipCards = [
    {
      title: "자기소개서 작성법",
      description: "나만의 이야기를 효과적으로 전달하는 방법을 알아보세요.",
      route: "/resume-guide",
    },
    {
      title: "면접 준비 전략",
      description: "실전 면접에서 자주 나오는 질문과 답변 전략을 확인하세요.",
      route: "/interview-prep",
    },
    {
      title: "포트폴리오 제작",
      description: "취업에 도움되는 포트폴리오 제작 가이드를 확인하세요.",
      route: "/portfolio-guide",
    },
  ];

  return (
    <div
      className="d-flex flex-column min-vh-100"
      style={{ width: "100vw", maxWidth: "none" }}
    >
      {/* Header */}
      <header
        className="d-flex justify-content-between align-items-center px-3 px-md-5 py-3 container-fluid"
        style={{ backgroundColor: mainColor }}
      >
        <img
          src="/images/logo.png"
          alt="Logo"
          className="cursor-pointer"
          style={{ height: "60px", cursor: "pointer" }}
          onClick={() => navigate("/")}
        />
        <div className="d-flex gap-2">
          {isLoggedIn ? (
            <>
              <button
                onClick={() => navigate("/chatbot")}
                className="btn btn-outline-light rounded-5 fw-bold"
              >
                챗봇
              </button>
              <button
                onClick={handleLogout}
                className="btn btn-light rounded-5 fw-bold"
                style={{ color: mainColor }}
              >
                로그아웃
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => navigate("/login")}
                className="btn btn-outline-light rounded-5 fw-bold"
              >
                로그인
              </button>
              <button
                onClick={() => navigate("/signup")}
                className="btn btn-light rounded-5 fw-bold"
                style={{ color: mainColor }}
              >
                회원가입
              </button>
            </>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-grow-1 w-100 mt-3 px-3 px-md-5">
        {/* Chatbot Image Section */}
        <section className="my-4 text-center">
          <img
            src="/images/chatbot_main.png"
            alt="Chatbot Introduction"
            className="img-fluid rounded mx-auto d-block"
            style={{
              maxHeight: "300px",
              objectFit: "cover",
              width: "100%",
              maxWidth: "1250px",
            }}
          />
        </section>

        {/* Job Search Tips Section */}
        <section className="py-2 mx-auto" style={{ maxWidth: "1200px" }}>
          <h5 className="fw-bold mb-4 text-start" style={{ color: grayColor }}>
            취업 준비 TIP!
          </h5>
          <div className="row justify-content-center">
            {tipCards.map((card, index) => (
              <div key={index} className="col-md-4 mb-3">
                <button
                  onClick={() => navigate(card.route)}
                  className="btn btn-white w-100 border shadow-sm p-3 py-4 rounded-4 d-flex flex-column align-items-center gap-2 text-center"
                  style={{ color: mainColor }}
                >
                  <h3 className="fs-5 fw-bold" style={{ color: mainColor }}>
                    {card.title}
                  </h3>
                  <p className="text-muted">{card.description}</p>
                </button>
              </div>
            ))}
          </div>
        </section>
      </main>

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
  );
};

export default Main;
