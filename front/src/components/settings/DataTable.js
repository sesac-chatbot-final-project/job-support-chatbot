import React from "react";

export const DataTable = ({ headers, data, renderActions }) => {
  return (
    <div className="table-responsive">
      <table className="table">
        <thead>
          <tr>
            {headers.map((header, index) => (
              <th key={index}>{header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((item) => (
            <tr key={item.id}>
              {Object.keys(item)
                .filter((key) => key !== "id")
                .map((key, index) => (
                  <td key={index}>{item[key]}</td>
                ))}
              <td>{renderActions(item)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
