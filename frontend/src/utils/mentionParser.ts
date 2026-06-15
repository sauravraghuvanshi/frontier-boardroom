/**
 * Mention parser for prep mode delegation
 *
 * Parses @mention syntax to extract agent names (CEO, CFO, CMO, CTO, Legal)
 * case-insensitively and deduplicated.
 *
 * Usage:
 *   const { mentions, cleanText } = parseMentions("@CTO what's the tech spend for SEA?");
 *   // => { mentions: ["CTO"], cleanText: "what's the tech spend for SEA?" }
 */

const VALID_ROLES = ["CEO", "CFO", "CMO", "CTO", "Legal"] as const;

export type Role = (typeof VALID_ROLES)[number];

const ROLE_BY_UPPER: Record<string, Role> = VALID_ROLES.reduce(
  (acc, r) => {
    acc[r.toUpperCase()] = r;
    return acc;
  },
  {} as Record<string, Role>,
);

export interface MentionParseResult {
  mentions: Role[];
  cleanText: string;
}

/**
 * Parse @mentions from text.
 *
 * Regex matches @AGENT (case-insensitive) where AGENT is a valid role.
 * Returns deduplicated mentions in canonical case and text with the @ROLE
 * tokens stripped so the agent sees a bare question.
 */
export function parseMentions(text: string): MentionParseResult {
  const mentionRegex = /@(CEO|CFO|CMO|CTO|Legal)\b/gi;
  const mentions = new Set<Role>();
  let match: RegExpExecArray | null;

  while ((match = mentionRegex.exec(text)) !== null) {
    const canonical = ROLE_BY_UPPER[match[1].toUpperCase()];
    if (canonical) mentions.add(canonical);
  }

  const cleanText = text.replace(mentionRegex, "").replace(/\s{2,}/g, " ").trim();

  return {
    mentions: Array.from(mentions),
    cleanText,
  };
}

/**
 * Check if a string contains any valid @mentions.
 */
export function hasMentions(text: string): boolean {
  const regex = /@(CEO|CFO|CMO|CTO|Legal)\b/i;
  return regex.test(text);
}

/**
 * Highlight mentions for visual feedback (returns marked-up text with a data attribute)
 *
 * Usage: useful for UI rendering later if we want to highlight @mentions as user types
 */
export function highlightMentions(text: string): string {
  return text.replace(
    /@(CEO|CFO|CMO|CTO|Legal)\b/gi,
    '<span class="mention">@$1</span>'
  );
}
