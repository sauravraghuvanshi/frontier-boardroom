/**
 * Mention parser for prep mode delegation
 *
 * Parses @mention syntax to extract agent names (CEO, CFO, CMO, CTO, Legal)
 * case-insensitively and deduplicated.
 *
 * Usage:
 *   const { mentions, cleanText } = parseMentions("@CTO what's the tech spend for SEA?");
 *   // => { mentions: ["CTO"], cleanText: "@CTO what's the tech spend for SEA?" }
 */

const VALID_ROLES = ["CEO", "CFO", "CMO", "CTO", "Legal"] as const;

export type Role = (typeof VALID_ROLES)[number];

export interface MentionParseResult {
  mentions: Role[];
  cleanText: string;
}

/**
 * Parse @mentions from text.
 *
 * Regex matches @AGENT (case-insensitive) where AGENT is a valid role.
 * Returns deduplicated mentions and the original text.
 */
export function parseMentions(text: string): MentionParseResult {
  const mentionRegex = /@(CEO|CFO|CMO|CTO|Legal)\b/gi;
  const mentions = new Set<Role>();
  let match: RegExpExecArray | null;

  while ((match = mentionRegex.exec(text)) !== null) {
    const role = match[1].toUpperCase() as Role;
    if ((VALID_ROLES as readonly string[]).includes(role)) {
      mentions.add(role);
    }
  }

  return {
    mentions: Array.from(mentions),
    cleanText: text,
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
