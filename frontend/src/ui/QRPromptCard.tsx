import { QRCodeSVG } from "qrcode.react";

export function QRPromptCard() {
  const url =
    (import.meta.env.VITE_AUDIENCE_URL as string | undefined) ||
    `${window.location.origin}/audience-question`;
  return (
    <div className="border-t border-white/10 p-3 flex gap-3 items-center">
      <QRCodeSVG value={url} size={72} bgColor="#11141b" fgColor="#7dd3fc" />
      <div className="text-xs text-white/60">
        <div className="uppercase tracking-wider mb-1">Audience Q</div>
        <div>Scan to submit a live question.</div>
      </div>
    </div>
  );
}
