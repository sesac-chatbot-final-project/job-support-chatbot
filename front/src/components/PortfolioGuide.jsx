import React from "react";
import { useNavigate } from "react-router-dom";
import "bootstrap/dist/css/bootstrap.min.css";

const PortfolioGuide = () => {
  const navigate = useNavigate();
  const mainColor = "#5e6aec";

  const portfolioSections = [
    {
      title: "포폴 필수 섹션",
      items: [
        "자기소개 및 연락처",
        "기술 스택",
        "프로젝트 경험",
        "교육 이력",
        "수상 및 자격증",
      ],
    },
    {
      title: "프로젝트 작성법",
      items: [
        "프로젝트 개요",
        "사용 기술",
        "본인 역할",
        "문제 해결 과정",
        "결과 및 성과",
      ],
    },
    {
      title: "차별화 전략",
      items: [
        "시각적 디자인",
        "데모/영상 추가",
        "코드 저장소 링크",
        "실제 운영 URL",
        "피드백 반영 내용",
      ],
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
          className="h-50 cursor-pointer"
          onClick={() => navigate("/")}
        />
        <button
          onClick={() => navigate("/")}
          className="btn btn-outline-light rounded-4"
        >
          홈으로
        </button>
      </header>

      {/* Main Content */}
      <main className="flex-grow-1 container-fluid px-3 px-md-5 py-5">
        <h3 className="text-center fw-bold mb-4" style={{ color: mainColor }}>
          포트폴리오 제작 가이드
        </h3>

        <div className="row g-4">
          {portfolioSections.map((section, index) => (
            <div key={index} className="col-md-4">
              <div className="card shadow-sm p-3 border-0 rounded-4">
                <div className="card-body">
                  <h2
                    className="fs-5 fw-bold mb-3"
                    style={{ color: mainColor }}
                  >
                    {section.title}
                  </h2>
                  <ul className="list-unstyled text-muted">
                    {section.items.map((item, itemIndex) => (
                      <li
                        key={itemIndex}
                        className="d-flex align-items-center mb-2"
                      >
                        <span className="me-2" style={{ color: mainColor }}>
                          •
                        </span>{" "}
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-5 p-4 bg-light rounded-4">
          <h3 className="fw-bold mb-3">포트폴리오 작성 예시</h3>
          <div className="p-3 bg-white rounded-4 shadow-sm">
            <h5 className="fw-bold mb-3 py-2 px-3">프로젝트 설명 예시</h5>
            <ul className="list-unstyled text-muted px-3">
              <li>
                <strong>• 프로젝트명:</strong> AI 기반 취업 지원 서비스
              </li>
              <li>
                <strong>• 개발 기간:</strong> 2024.01 - 2024.03 (3개월)
              </li>
              <li>
                <strong>• 사용 기술:</strong> React, Node.js, MongoDB, AWS
              </li>
              <li>
                <strong>• 주요 기능:</strong> 자기소개서 분석, 모의 면접, 채용
                정보 제공
              </li>
              <li>
                <strong>• 본인 역할:</strong> 프론트엔드 개발 및 UI/UX 디자인
              </li>
              <li>
                <strong>• 성과:</strong> 사용자 만족도 92%, 월간 활성 사용자
                5,000명 달성
              </li>
            </ul>
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
            style={{ fontSize: "12px", lineHeight: "1.1" }}
          >
            고객센터
          </button>
          <button
            onClick={() => navigate("/terms")}
            className="btn btn-link text-secondary"
            style={{ fontSize: "12px", lineHeight: "1.1" }}
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

export default PortfolioGuide;
