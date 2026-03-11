import React, { useEffect, useState } from "react";
import { BaseViewerProps } from "./types";
import { useI18n } from "@/context/LanguageContext";

export const ChartViewer: React.FC<BaseViewerProps> = ({ content, style }) => {
  const { t } = useI18n();
  const [imageUrl, setImageUrl] = useState<string>("");

  useEffect(() => {
    // Try to parse URL in content
    try {
      // If content itself is a URL
      if (content.startsWith("http")) {
        setImageUrl(content);
      } else {
        // If content contains URL (e.g., in JSON)
        const matches = content.match(/(https?:\/\/[^\s"]+)/g);
        if (matches && matches.length > 0) {
          setImageUrl(matches[0]);
        }
      }
    } catch (error) {
      console.error("Error parsing chart URL:", error);
    }
  }, [content]);

  if (!imageUrl) {
    return <div>{t("viewer.chartInvalid")}</div>;
  }

  return (
    <div
      style={{
        display: "flex",
        flex: 1,
        position: "relative",
        overflow: "hidden",
        justifyContent: "center",
        alignItems: "center",
        padding: "20px",
        ...style,
      }}
    >
      <img
        src={imageUrl}
        alt={t("viewer.chartAlt")}
        style={{
          maxWidth: "100%",
          maxHeight: "100%",
          objectFit: "contain",
        }}
        onError={(e) => {
          console.error("Error loading chart image");
          e.currentTarget.style.display = "none";
        }}
      />
    </div>
  );
};
