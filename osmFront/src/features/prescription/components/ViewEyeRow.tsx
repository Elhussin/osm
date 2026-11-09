import React from "react";


const EyeRowView: React.FC<{ side: "right" | "left"; data: any }> = ({ side, data }) => {
    const prefix = side === "right" ? "R" : "L";
    return (
      <div className="grid grid-cols-[80px_repeat(4,1fr)] gap-2">
        <div className="flex items-center">
          <h3 className="text-lg font-semibold">{prefix}</h3>
        </div>

        <div><p className="input-text" >{data[`${side}_sphere`] ?? "-"} </p></div>
        <div><p className="input-text" >{data[`${side}_cylinder`] ?? "-"} </p> </div>
        <div> <p className="input-text" >{data[`${side}_axis`] ?? "-"} </p> </div>
        <div><p className="input-text" >{data[`${side}_reading_add`] ?? "-"} </p> </div>

      </div>
    );
  };

  export default EyeRowView;  