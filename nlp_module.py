import re
from sklearn.feature_extraction.text import TfidfVectorizer


def clean_transcript(text):
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_sentences(text):
    return re.split(r"(?<=[.!?])\s+", text)


def generate_summary(transcript, number_of_sentences=3):
    text = clean_transcript(transcript)
    sentences = split_sentences(text)
    sentences = [s for s in sentences if len(s.split()) > 3]

    if not sentences:
        return "No transcript available."

    if len(sentences) <= number_of_sentences:
        return " ".join(sentences)

    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        matrix = vectorizer.fit_transform(sentences)
        scores = matrix.sum(axis=1).A1

        best = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:number_of_sentences]

        best.sort()
        return " ".join(sentences[i] for i in best)

    except ValueError:
        return " ".join(sentences[:number_of_sentences])


def extract_decisions(transcript):
    keywords = [
        "decided", "agreed", "approved",
        "confirmed", "finalized", "finalised"
    ]

    return [
        sentence
        for sentence in split_sentences(clean_transcript(transcript))
        if any(word in sentence.lower() for word in keywords)
    ]


def process_meeting(transcript):
    return {
        "summary": generate_summary(transcript),
        "decisions": extract_decisions(transcript),
        "transcript": clean_transcript(transcript)
    }


if __name__ == "__main__":
    sample = """
    The team discussed the Belvo Minutes project.
    Deepak agreed to complete audio processing.
    Akash will handle speech to text.
    Praveen will develop the summarisation module.
    The team decided to finish the first version today.
    """

    result = process_meeting(sample)

    print("BELVO MINUTES RESULTS")
    print("SUMMARY:", result["summary"])
    print("DECISIONS:", result["decisions"])