import { NextRequest, NextResponse } from "next/server";

const GEMINI_API_KEY = process.env.GEMINI_API_KEY;
const GEMINI_URL = `https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key=${GEMINI_API_KEY}`;

function cleanTranslatedText(value: string): string {
  return value
    .replace(/```(?:text|json)?/gi, "")
    .replace(/```/g, "")
    .replace(/^english\s*translation\s*:\s*/i, "")
    .replace(/^translation\s*:\s*/i, "")
    .trim();
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const text = typeof body.text === "string" ? body.text.trim() : "";
    const sourceLanguage = typeof body.sourceLanguage === "string" ? body.sourceLanguage : "ta-IN";

    if (!text) {
      return NextResponse.json({ error: "No transcript provided." }, { status: 400 });
    }

    if (!GEMINI_API_KEY) {
      return NextResponse.json({ error: "Gemini API key is not configured." }, { status: 500 });
    }

    // Call Gemini 1.5 Flash to translate Tamil / English / Tanglish speech into clear English
    const prompt = `Translate this patient speech transcript into clear, clinical English. The speech may be in Tamil, English, or a mix of both (Tanglish).

Rules:
- Translate all Tamil/Tanglish phrases to clear English.
- Polish any broken English to be grammatically correct and clinical.
- Preserve all medical details (symptoms, durations, body parts, medications, doctor suggestions, tests, daily routine details, sleep).
- Do not diagnose or prescribe.
- Do not add new clinical facts.
- Return ONLY the final translated English text. Do not include introductory or explanatory text.

Patient Speech Transcript:
"${text}"`;

    const requestBody = {
      contents: [{
        parts: [{ text: prompt }]
      }],
      generationConfig: {
        temperature: 0.2,
        maxOutputTokens: 1024,
      }
    };

    const res = await fetch(GEMINI_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestBody),
    });

    if (!res.ok) {
      const errorText = await res.text();
      console.error("Gemini translation call failed:", errorText);
      return NextResponse.json({ error: "Translation service failed." }, { status: 502 });
    }

    const data = await res.json();
    const raw = data?.candidates?.[0]?.content?.parts?.[0]?.text;
    const translatedText = typeof raw === "string" ? cleanTranslatedText(raw) : "";

    return NextResponse.json({
      originalText: text,
      translatedText: translatedText || text,
      sourceLanguage,
    });
  } catch (error) {
    console.error("Voice translation failed:", error);
    return NextResponse.json({ error: "Voice translation failed." }, { status: 500 });
  }
}
