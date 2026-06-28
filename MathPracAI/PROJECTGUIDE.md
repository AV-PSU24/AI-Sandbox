# MathPracAI - Product Vision & Current Direction

  ## Project Purpose

  MathPracAI is being built to solve a real tutoring problem.

  I currently tutor one Algebra 2 student. One of the biggest challenges is finding enough quality practice problems after introducing a new topic. Existing worksheets are often:

  * Paid
  * Difficult to find
  * Poorly formatted
  * Limited in quantity
  * Not personalized to the student's needs

  The goal of MathPracAI is **not** to become another worksheet website.

  The goal is to build a **practice engine** capable of generating unlimited, high-quality practice while tracking student learning over time.

  ---

  # Long-Term Vision

  The long-term vision is for MathPracAI to become an intelligent practice platform.

  A student should be able to log in every day (similar to the consistency of Wordle), complete a short personalized practice session, and gradually master Algebra 2 through consistent review and spaced
  repetition.

  Eventually the system should:

  * Generate unlimited valid practice problems.
  * Track every student interaction.
  * Identify strengths and weaknesses.
  * Recommend future review topics.
  * Help tutors understand exactly where a student is struggling.

  The engine should focus on helping students **learn**, not simply complete worksheets.

  ---

  # Current MVP

  The current version focuses on one student and three Algebra 2 topics:

  1. Evaluating Functions
  2. Domain and Range
  3. Parent Functions

  The UI is intentionally simple for now.

  Current development should prioritize:

  1. Clean problem presentation.
  2. Reliable problem generation.
  3. Expandability.

  UI polish can come later.

  ---

  # Core Design Philosophy

  The most important design principle is:

  **Generate infinite valid problems.**

  Instead of hardcoding hundreds of problems, MathPracAI should model the mathematics itself.

  Every problem should be generated from reusable templates and mathematical rules.

  This allows:

  * Unlimited practice
  * Reliable answer keys
  * Consistent difficulty
  * Easy expansion to new topics

  The engine should never depend on AI for mathematical correctness.

  ---

  # Future AI Philosophy

  AI will eventually improve the learning experience, but it should not determine mathematical correctness.

  Potential AI responsibilities:

  * Better explanations
  * Personalized hints
  * Review recommendations
  * Adaptive practice
  * Word problem generation

  The mathematical engine should remain deterministic and reliable.

  ---

  # Current Focus

  At this stage we are NOT designing graph assets yet.

  The current goal is to establish:

  * Problem templates
  * Text layout
  * Problem presentation
  * Engine architecture

  Graph assets will be designed afterward.

  ---

  # Problem Template Philosophy

  Every problem should have a consistent structure.

  Each problem contains:

  * Display content
  * Prompt
  * Student answer area
  * Metadata (topic, difficulty, etc.)

  This consistent structure will allow future graph assets to plug into the same system.

  ---

  # Topic 1 — Evaluating Functions

  Current display format:

  Example:

  f(x) = x² - 2x + 8

  Evaluate f(3).

  NOT:

  Evaluate f(3) if f(x) = x² - 2x + 8.

  The equation should always be displayed first.

  The prompt should appear underneath.

  This makes the problems cleaner, easier to scan, and more worksheet-like.

  Future versions may include:

  * Linear
  * Quadratic
  * Absolute value
  * Square root
  * Piecewise
  * Composition of functions

  For now, only linear and quadratic evaluation problems are required.

  ---

  # Topic 2 — Domain and Range

  Current display format:

  Example:

  f(x) = x² - 2x + 8

  Domain: __________

  Range: __________

  The equation should always appear first.

  The answer blanks should be underneath.

  No graph assets yet.

  Future versions will support:

  * Equation-based problems
  * Graph-based problems
  * Table-based problems

  Only equation-based problems are currently in scope.

  ---

  # Topic 3 — Parent Functions

  Parent Functions will be implemented later.

  The long-term vision is much larger than static graphs.

  Eventually the application should include a Desmos-like interactive graph.

  Desired future functionality:

  * Zoom
  * Pan
  * Grid
  * Plot points
  * Draw on graph
  * Interactive graph questions

  Because this requires significantly more infrastructure, Parent Functions will be implemented after the text-based engine is complete.

  ---

  # Current Development Priorities

  Priority 1:
  Create clean, reusable text-based problem templates.

  Priority 2:
  Design the underlying problem generation engine.

  Priority 3:
  Introduce graph assets.

  Priority 4:
  Build interactive graph functionality.

  Everything should be built with future expansion in mind while keeping the current implementation simple and maintainable.
