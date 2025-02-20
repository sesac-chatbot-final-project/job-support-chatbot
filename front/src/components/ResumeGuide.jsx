import React from "react";
import { useNavigate } from "react-router-dom";
import "bootstrap/dist/css/bootstrap.min.css";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faHome } from "@fortawesome/free-solid-svg-icons";

const ResumeGuide = () => {
  const navigate = useNavigate();
  const mainColor = "#5e6aec";
  const fontFamily = { fontFamily: "Noto Sans, sans-serif" };

  const guideContent = [
    {
      title: "자기소개서 기본 구조",
      content:
        "• 성장 과정\n• 지원 동기\n• 입사 후 포부\n•  프로젝트/경험 기술",
    },
    {
      title: "작성 꿀팁",
      content:
        "• 구체적인 사례 중심으로 작성\n•  성과는 수치화하여 표현\n•  회사의 가치관과 연계\n•  간결하고 명확한 문장 사용",
    },
    {
      title: "피해야 할 사항",
      content:
        "• 추상적인 표현 지양\n•  과도한 미사여구 자제\n•  불필요한 내용 나열\n•  타인과의 비교",
    },
  ];

  return (
    <div
      className="d-flex flex-column min-vh-100"
      style={{ width: "100vw", maxWidth: "none" }}
    >
      {/* Header */}
      <header
        className="d-flex justify-content-between align-items-center px-4 py-3 container-fluid px-0"
        style={{ backgroundColor: mainColor, ...fontFamily }}
      >
        <div
          className="container d-flex justify-content-between align-items-center"
          style={{ maxWidth: "1200px" }}
        >
          <img
            src="/images/logo.png"
            alt="Logo"
            className="h-50 cursor-pointer"
            onClick={() => navigate("/")}
            style={{ cursor: "pointer" }}
          />
          <button
            onClick={() => navigate("/")}
            className="btn rounded-5 fw-bold"
          >
            <FontAwesomeIcon
              icon={faHome}
              style={{
                color: "white",
                border: "none",
                width: "1.4rem",
                height: "1.4rem",
              }}
            />
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main
        className="flex-grow-1 container-fluid px-3 px-md-5 py-5 d-flex justify-content-center"
        style={{ width: "100vw", maxWidth: "none", ...fontFamily }}
      >
        <div className="container" style={{ maxWidth: "1200px" }}>
          <h3 className="text-center fw-bold mb-4" style={{ color: mainColor }}>
            자기소개서 작성 가이드
          </h3>

          <div className="row g-4 mb-4">
            {guideContent.map((section, index) => (
              <div key={index} className="col-md-4">
                <div className="card shadow-sm p-3 border-0 rounded-4">
                  <div className="card-body">
                    <h2
                      className="fs-5 fw-bold mb-3"
                      style={{ color: mainColor }}
                    >
                      {section.title}
                    </h2>
                    <pre
                      className="text-muted whitespace-pre-line"
                      style={fontFamily}
                    >
                      {section.content}
                    </pre>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="p-4 bg-light rounded-4" style={fontFamily}>
            <h5
              className="fw-bold mb-3 px-4"
              style={{ fontFamily, color: mainColor }}
            >
              실전 예시
            </h5>
            <div className="p-3 bg-white rounded-4 shadow-sm">
              <h3
                className="fs-6 fw-bold mb-2 px-3 mt-3"
                style={{ fontFamily, color: "GrayText" }}
              >
                참고하기 좋은 예시
              </h3>
              <p className="text-muted px-4 py-1" style={fontFamily}>
                " 대학 시절 프로젝트 리더로서 6명의 팀원들과 함께 교내 창업
                경진대회에서 대상을 수상했습니다. 프로젝트 기간 동안 주 3회
                미팅을 통해 진행 상황을 공유하고, 문제 발생 시 즉각적인 해결
                방안을 모색하여 초기 계획 대비 일정을 98% 준수할 수 있었습니다."
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer
        className="bg-light py-4 container-fluid px-0"
        style={{ width: "100vw", maxWidth: "none" }}
      >
        <div
          className="container d-flex justify-content-center gap-3"
          style={{ maxWidth: "1200px" }}
        >
          <button
            onClick={() => navigate("/customer-support")}
            className="btn btn-link text-secondary"
            style={{ fontSize: "16px", lineHeight: "1.1" }}
          >
            고객센터
          </button>
          <button
            onClick={() => navigate("/terms")}
            className="btn btn-link text-secondary"
            style={{ fontSize: "16px", lineHeight: "1.1" }}
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

export default ResumeGuide;
