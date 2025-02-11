import React from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faSignInAlt, faSignOutAlt } from "@fortawesome/free-solid-svg-icons";

export const Profile = ({
  isLoggedIn,
  userProfile,
  handleLogout,
  handleLogin,
  mainColor,
}) => {
  return (
    <div className="bg-white p-4 rounded-3 shadow-sm">
      <h3 className="mb-4">내 정보</h3>
      {isLoggedIn ? (
        <>
          {Object.entries({
            이름: userProfile.name,
            이메일: userProfile.email,
            전화번호: userProfile.phone,
            "희망 직무": userProfile.position,
            경력: userProfile.career,
          }).map(([key, value]) => (
            <div key={key} className="row mb-3">
              <div className="col-md-3 fw-bold">{key}</div>
              <div className="col-md-9">{value}</div>
            </div>
          ))}
          <div className="d-flex gap-2">
            <button
              className="btn mt-3"
              style={{
                backgroundColor: mainColor,
                color: "white",
              }}
            >
              프로필 수정
            </button>
            <button
              className="btn btn-outline-danger mt-3"
              onClick={handleLogout}
            >
              <FontAwesomeIcon icon={faSignOutAlt} className="me-2" />
              로그아웃
            </button>
          </div>
        </>
      ) : (
        <div className="text-center py-5">
          <h4 className="mb-4">로그인이 필요한 서비스입니다</h4>
          <p className="text-muted mb-4">
            로그인하시면 내 정보 확인 및 수정이 가능합니다
          </p>
          <button
            className="btn"
            style={{
              backgroundColor: mainColor,
              color: "white",
            }}
            onClick={handleLogin}
          >
            <FontAwesomeIcon icon={faSignInAlt} className="me-2" />
            로그인하기
          </button>
        </div>
      )}
    </div>
  );
};
