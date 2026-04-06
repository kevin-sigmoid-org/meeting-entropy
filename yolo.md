# 🦞 The Great Hallucination Exorcism of April 2026

## Context

On April 6th, 2026 at approximately 11:47 PM, meeting-entropy was 
officially diagnosed with **Acute Whisper Hallucination Syndrome** 
(AWHS), a rare but devastating condition where the transcription 
engine starts inventing French existentialist poetry instead of 
transcribing actual speech.

Symptoms observed:
- "Je suis enceau de la putain de la vie" (nobody said that)
- "Faut réclerce, faut réclerce, faut réclerce" (nobody said that either)
- "On va prendre la verte au quick" (still, nobody)
- "I hope I will never send it to you" (getting philosophical now)
- "what does any good..." (deeply concerning)

## Root Cause Analysis

After a 4-hour forensic investigation conducted by Julien Mer 
and his trusty AI sidekick, three layered bugs were identified:

1. **The Path of Broken Dreams**: `WhisperModel` was receiving 
   an absolute filesystem path instead of a model name, causing 
   silent failures on missing models.

2. **The i3-7th-Gen Tragedy**: Running Whisper small/medium on 
   a 2017 dual-core CPU is like asking a hamster to pull a 
   freight train. Technically possible, ethically questionable.

3. **The Hallucination Cascade**: Whisper tiny in French mode 
   has a PhD in creative writing and will happily invent 
   entire sentences from 3 seconds of background noise.

## The Fix

We performed a complete spiritual and technical migration from 
`faster-whisper` to **Vosk**, a Kaldi-based ASR engine that has 
the revolutionary property of **only transcribing words that 
were actually spoken**.

Key improvements:
- ✅ Zero hallucinations (Vosk refuses to dream)
- ✅ 10x faster on potato hardware
- ✅ Streaming PartialResult support
- ✅ Auto-detection of machine tier (tiny/small/medium/large)
- ✅ Native support for bullshit in both English and French

## Test Results

**Before:**
> Entropy: 0.0% | Total hits: 0 | Last transcript: "Je suis enceau..."

**After:**
> Entropy: 100.0% | Total hits: 2 | Last transcript: "c'est noté"

A single "c'est noté" was enough to max out the entropy meter, 
which is either a triumph of calibration or a damning indictment 
of French corporate culture. Possibly both.

## Acknowledgments

- **Kevin Sigmoid** — for believing in us when the tests didn't
- **RaiMan** — for not being involved in this one, for once
- **The i3 7th gen** — for surviving another day
- **Vosk** — for refusing to hallucinate, unlike certain transformers
- **Coffee** — the real MVP

## Breaking Changes

None. The class is still called `MicrophoneWhisperer` out of 
pure spite and commitment to backwards compatibility. It no 
longer whispers anything. It voskers. Deal with it.

---

*"In a world full of hallucinating LLMs, be a Kaldi recognizer."*  
— Kevin Sigmoid, Philosopher-in-Residence, 🦞