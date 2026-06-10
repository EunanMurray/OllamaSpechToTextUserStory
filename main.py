import sys
import config
from stt import record_and_transcribe
from llm import generate_user_story, get_clarifying_questions

DIVIDER = "-" * 60


def print_header():
    print()
    print("=" * 60)
    print("  Voice to User Story")
    print("=" * 60)
    print()


def collect_clarifications(transcript: str):
    """Ask the LLM for gaps, then let the user answer each question."""
    try:
        questions = get_clarifying_questions(transcript)
    except Exception as e:
        print(f"(Skipping clarification — {e})")
        return []

    if not questions:
        return []

    print()
    print(DIVIDER)
    print("A few questions to sharpen the story:")
    print("(type an answer, 'v' to speak it, or ENTER to skip)")
    print(DIVIDER)

    answers = []
    for i, question in enumerate(questions, 1):
        print(f"\n  {i}. {question}")
        reply = input("     > ").strip()

        if reply == "":
            continue
        if reply.lower() == "v":
            answer = record_and_transcribe()
            if not answer:
                print("     (no speech detected, skipping)")
                continue
            print(f"     heard: {answer}")
            answers.append((question, answer))
        else:
            answers.append((question, reply))

    return answers


def main():
    print_header()

    while True:
        try:
            transcript = record_and_transcribe()
        except KeyboardInterrupt:
            print("\nExiting.")
            sys.exit(0)

        if not transcript:
            print("No speech detected. Try again.\n")
            continue

        print()
        print(DIVIDER)
        print("Transcript:")
        print(f"  {transcript}")
        print(DIVIDER)

        clarifications = []
        if config.ENABLE_CLARIFICATION:
            clarifications = collect_clarifications(transcript)

        print()
        print("Generating user story...", flush=True)
        try:
            story = generate_user_story(transcript, clarifications)
        except Exception as e:
            print(f"Error talking to Ollama: {e}")
            continue

        print()
        print("=" * 60)
        print("  User Story")
        print("=" * 60)
        print(story)
        print("=" * 60)
        print()

        again = input("Record another? [Y/n]: ").strip().lower()
        if again in ("n", "no"):
            print("Done.")
            break
        print()


if __name__ == "__main__":
    main()
