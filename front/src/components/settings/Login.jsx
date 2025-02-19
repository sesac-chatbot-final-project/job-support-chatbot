// src/components/settings/Profile.js
import React from "react";

export const Profile = ({
  isLoggedIn,
  userProfile,
  handleLogin,
  handleLogout,
  mainColor,
}) => {
  // 로그인하지 않았거나 userProfile이 아직 로드되지 않은 경우
  if (!isLoggedIn || !userProfile) {
    return (
      <div
        className="bg-white p-4 rounded-3 text-center mb-5 mt-5"
        style={{ minHeight: "550px", maxWidth: "600px", margin: "auto" }}
      >
        <h3 className="mb-4 text-center mt-3" style={{ color: "GrayText" }}>
          {" "}
          <strong>로그인 필요</strong>
        </h3>
        <p
          className="text-center"
          style={{ fontSize: "18px", color: "GrayText" }}
        >
          로그인 후 이용 가능합니다.
        </p>
        <div className="text-center">
          <button
            className="btn rounded-5 text-center mt-2 py-2 px-4 fw-bold"
            onClick={handleLogin}
            style={{
              backgroundColor: mainColor,
              color: "white",
              fontSize: "18px",
            }}
          >
            로그인
          </button>
        </div>
      </div>
    );
  }

  // 로그인된 상태라면 사용자 정보를 표시합니다.
  return (
    <div
      className="bg-white py-5 px-5 rounded-5 mb-5 mt-5 "
      style={{ minHeight: "550px", maxWidth: "600px", margin: "auto" }}
    >
      <h4 className="mb-4 p-2 text-center">
        <strong>내 프로필</strong>
      </h4>
      <p className="text-center">
        <strong>아이디:</strong> {userProfile.name}
      </p>
      <div className="text-center mt-5 ">
        <button
          className="btn btn-outline-danger rounded-5"
          onClick={handleLogout}
        >
          로그아웃
        </button>
      </div>
    </div>
  );
};
