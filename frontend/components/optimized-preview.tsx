"use client";

interface OptimizedPreviewProps {
  text: string;
  sections: Record<string, string>;
  highlights?: Set<string>;
}

function parseSections(text: string): { header: string[]; sections: { title: string; lines: string[] }[] } {
  const lines = text.split("\n");
  const header: string[] = [];
  const sections: { title: string; lines: string[] }[] = [];
  let current: { title: string; lines: string[] } = { title: "", lines: [] };
  let bodyStarted = false;

  for (const line of lines) {
    const stripped = line.trim();
    if (!stripped) {
      if (bodyStarted) current.lines.push("");
      continue;
    }

    const alphaChars = stripped.replace(/[^a-zA-ZğüşıöçĞÜŞİÖÇ]/g, "");
    const isHeader =
      alphaChars.length >= 3 &&
      stripped === stripped.toUpperCase() &&
      /[A-ZĞÜŞİÖÇ]/.test(stripped) &&
      !stripped.startsWith("•") &&
      !stripped.startsWith("-");

    if (isHeader) {
      bodyStarted = true;
      if (current.title || current.lines.length) sections.push(current);
      current = { title: stripped, lines: [] };
    } else if (!bodyStarted) {
      header.push(stripped);
    } else {
      current.lines.push(stripped);
    }
  }
  if (current.title || current.lines.length) sections.push(current);

  return { header, sections };
}

export function OptimizedPreview({ text, sections: sectionDict, highlights }: OptimizedPreviewProps) {
  // sections dict varsa onu kullan, yoksa metni parse et
  const hasSections = sectionDict && Object.keys(sectionDict).length > 1;

  if (hasSections) {
    return (
      <div className="rounded-lg bg-white p-6 text-black shadow-inner max-h-[calc(100vh-280px)] overflow-y-auto">
        {Object.entries(sectionDict).map(([name, content], i) => (
          <div key={name} className={i > 0 ? "mt-4 border-t border-gray-200 pt-4" : ""}>
            <h3 className="mb-2 text-[13px] font-bold uppercase tracking-wide text-gray-800">
              {name}
            </h3>
            {String(content)
              .split("\n")
              .map((line, j) => {
                const stripped = line.trim();
                if (!stripped) return <div key={j} className="h-2" />;
                const isBullet = /^[•\-*–]/.test(stripped);
                const isHighlighted = highlights?.has(stripped);
                return (
                  <p
                    key={j}
                    className={`text-[10.5px] leading-[1.4] text-gray-700 ${
                      isBullet ? "ml-3" : ""
                    } ${isHighlighted ? "bg-green-100 rounded px-1" : ""}`}
                  >
                    {isBullet ? `•  ${stripped.replace(/^[•\-*–]\s*/, "")}` : stripped}
                  </p>
                );
              })}
          </div>
        ))}
      </div>
    );
  }

  // Text parse mode
  const { header, sections: parsed } = parseSections(text);

  return (
    <div className="rounded-lg bg-white p-6 text-black shadow-inner max-h-[calc(100vh-280px)] overflow-y-auto">
      {/* Header */}
      {header.length > 0 && (
        <div className="mb-4 text-center">
          <h2 className="text-lg font-bold text-gray-900">{header[0]}</h2>
          {header.length > 1 && (
            <p className="mt-1 text-[10px] text-gray-500">{header.slice(1).join(" | ")}</p>
          )}
        </div>
      )}

      {/* Sections */}
      {parsed.map((section, i) => (
        <div
          key={i}
          className={i > 0 || header.length > 0 ? "mt-4 border-t border-gray-200 pt-4" : ""}
        >
          {section.title && (
            <h3 className="mb-2 text-[13px] font-bold uppercase tracking-wide text-gray-800">
              {section.title}
            </h3>
          )}
          {section.lines.map((line, j) => {
            if (!line.trim()) return <div key={j} className="h-2" />;
            const isBullet = /^[•\-*–]/.test(line.trim());
            const isHighlighted = highlights?.has(line.trim());
            return (
              <p
                key={j}
                className={`text-[10.5px] leading-[1.4] text-gray-700 ${
                  isBullet ? "ml-3" : ""
                } ${isHighlighted ? "bg-green-100 rounded px-1" : ""}`}
              >
                {isBullet ? `•  ${line.trim().replace(/^[•\-*–]\s*/, "")}` : line.trim()}
              </p>
            );
          })}
        </div>
      ))}

      {!text && Object.keys(sectionDict || {}).length === 0 && (
        <p className="text-center text-sm text-gray-400 italic">Önizleme için öneri seçin</p>
      )}
    </div>
  );
}
