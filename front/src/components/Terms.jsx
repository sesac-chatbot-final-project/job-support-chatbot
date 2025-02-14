import React from "react";
import { useNavigate } from "react-router-dom";
import "bootstrap/dist/css/bootstrap.min.css";

const Terms = () => {
  const navigate = useNavigate();
  const mainColor = "#5e6aec";
  return (
    <div className="container my-7">
      {/* Header */}
      <header
        className="d-flex justify-content-between align-items-center px-4 py-3"
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
      <h3 className="text-center mb-4 px-6 py-4">이용 약관</h3>

      <p className="lead">
        서비스를 사용하기 전에 아래 이용 약관을 잘 읽어주세요.
      </p>

      <div>
        <h5>1. 약관 동의</h5>
        <p>
          본 웹사이트에 접속하고 사용하는 것은 이 이용 약관에 동의하는 것으로
          간주됩니다.
        </p>

        <h5>2. 개인정보 처리 방침</h5>
        <p>
          귀하의 개인정보는 중요하게 다뤄지며, 개인정보 처리 방침을 통해
          데이터를 어떻게 수집하고 사용하는지 확인할 수 있습니다.
        </p>

        <h5>3. 사용자 의무</h5>
        <p>
          귀하는 불법적인 목적으로 서비스를 사용하거나 서비스에 손해를 주는
          방식으로 사용하지 않을 것에 동의합니다.
        </p>

        <h5>4. 책임 제한</h5>
        <p>
          본 웹사이트를 사용함으로 인해 발생한 직접적, 간접적, 우발적, 결과적인
          손해에 대해 당사는 책임을 지지 않습니다.
        </p>

        <h5>5. 약관 변경</h5>
        <p>
          당사는 이 약관을 수시로 업데이트할 수 있으며, 귀하는 정기적으로 약관을
          검토할 책임이 있습니다.
        </p>
      </div>
    </div>
  );
};

export default Terms;
