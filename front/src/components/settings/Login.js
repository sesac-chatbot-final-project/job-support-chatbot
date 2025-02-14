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
        className="bg-white p-4 rounded-3 shadow-sm"
        style={{ maxWidth: "400px", margin: "auto" }}
      >
        <h3 className="mb-4 text-center">로그인 필요</h3>
        <p className="text-center">로그인 후 이용 가능합니다.</p>
        <div className="text-center">
          <button
            className="btn"
            onClick={handleLogin}
            style={{ backgroundColor: mainColor, color: "white" }}
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
      className="bg-white p-4 rounded-3 shadow-sm"
      style={{ maxWidth: "400px", margin: "auto" }}
    >
      <h3 className="mb-4 text-center">내 프로필</h3>
      <p>
        <strong>이름:</strong> {userProfile.name}
      </p>
      <p>
        <strong>이메일:</strong> {userProfile.email}
      </p>
      <p>
        <strong>전화번호:</strong> {userProfile.phone}
      </p>
      <p>
        <strong>직무:</strong> {userProfile.position}
      </p>
      <p>
        <strong>경력:</strong> {userProfile.career}
      </p>
      <div className="text-center">
        <button className="btn btn-outline-danger" onClick={handleLogout}>
          로그아웃
        </button>
      </div>
    </div>
  );
};
