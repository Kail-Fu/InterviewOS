# Real-Work Coding Assessment

Welcome! You’ve been invited to complete a short, real-world coding challenge designed to reflect the kind of work you might actually do on the job.

This assessment is being delivered through InterviewOS, a platform trusted by hiring teams to run realistic, AI-enhanced coding evaluations.

---

## 📋 What You Need to Know

- Your **screen and audio recording** has already started (via your browser).
- Please **do not close or refresh the assessment tab** — doing so will stop the recording and may void your submission.
- You may use **any AI tools** (e.g. ChatGPT, GitHub Copilot, etc.)
- This is a **solo** exercise — no pair programming or external help allowed.

If you encounter issues, contact our team at **[the assessment sender](mailto:the assessment sender)** immediately.

---

## 💻 What You’ll Work On

You’ll be working inside a small, realistic codebase in Node.js/Express. The goal is not to finish everything, but to make strong, thoughtful progress.

You’ll be working on the following 4 tasks — complete as many as you can within the time limit:

1. **Fix a Bug**  
   Currently, `GET /users/:id` returns **404 Not Found** in both of these cases:
   - When the user is not found.
   - When the `id` format is invalid (not a valid UUID v4).  
   
   Update the route so that:
   - If the `id` format is invalid → return **400 Bad Request**
   - If the `id` is valid but the user is not found → return **404 Not Found**

2. **Extend an API**  
   Add support for query filtering: `/users?status=active&team=marketing`

3. **Build a Feature**  
   Add `GET /users/inactive` to return users with no login activity in the last 30+ days.

4. **Write Tests**  
   Add integration tests for any endpoint.

---

## 📦 What to Submit

After the timer ends, the platform will ask you to:

1. 🎤 Record a **short reflection video** (up to 2 minutes) in your browser
2. 📁 Upload your modified project as a `.zip`

---

## 💡 What We’re Evaluating

We’re not just looking for perfect code. We’re looking at:
- Your ability to navigate a real codebase
- Your problem solving skills
- Coding skills as well as documentation clarity

---
## 📄 Note on `wiki.md`

There is an `wiki.md` file in the repository.  
It was last updated **several years ago** and may contain **inaccurate or outdated information**.  
Use it **only as a loose reference**, not as a definitive source of truth.

Good luck — we’re excited to see your thinking and approach!