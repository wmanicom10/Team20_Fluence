# Final Presentation Plan

## Objective
To successfully present the Fluence project, demonstrating our completed application architecture, AI features, and user workflows. This document outlines the structure of our final presentation, addressing all necessary items to meet the course requirements.

## Poster Contents
The poster will cover the key aspects of the project, including:
1. **Introduction & Motivation:** The public health problem we are solving with Fluence.
2. **System Architecture:** A high-level diagram illustrating the frontend (React/Vite), backend (Flask/Python), and database (Supabase) interactions.
3. **Resilient Offline Architecture:** Demonstration of how the frontend gracefully intercepts [Errno 11001] DNS resolution errors (caused by paused Supabase servers) and intelligently falls back to formatted, realistic mock data arrays without crashing the UI.
4. **Key Features Overview:** Highlights such as real-time disease dashboard tracking, AI risk scoring, and role-based access control.
5. **AI Integration:** An explanation of how the baseline AI model normalizes data, trains, and exposes risk scores.
6. **Challenges & Future Work:** What obstacles we overcame (e.g., integrating the Supabase API, handling async route guards, and mitigating live environment dead-links through resilient fallbacks) and what could be done next.

## Presentation Roles
The presentation will be divided evenly among team members:
- **Sebastian Lassander:** Introduction, architectural overview, and explanation of route protection/role gating workflows.
- **Will Manicom:** Deep dive into the user experience, authentication flow, and frontend design architecture.
- **Jason Riek:** Backend integration details, Supabase endpoint implementation, and the verification pipeline.
- **Ethan Batick:** Explanation of the AI system, model training process, and how risk output is consumed by the dashboard.

## Demo Plan
The live demonstration will walk through a standard primary user journey:
1. **Guest View:** Show the landing page and the guest access limitations (route guards redirecting appropriately).
2. **Authentication:** Log in as a newly registered user to demonstrate the secure flow.
3. **Health Official Features:** Show the verification request process and the gated 'Submit Case' form.
4. **Disease Dashboard:** Navigate to the main dashboard to view the map, toggle data views, and verify that the stats update. Explicitly demonstrate the offline mockup resilience kicking in to gracefully handle the external Supabase server being offline.
5. **AI Insights:** Highlight the AI risk summary card reacting to the fallback data to demonstrate the end-to-end user pipeline without breaking.
