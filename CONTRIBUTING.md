# Contributing to Regtura

Thank you for your interest in contributing to Regtura. This project sits at the intersection of regulatory reporting and AI, and we welcome contributions from both domains.

## How to contribute

### Reporting bugs

If you find a bug, please open a [GitHub Issue](../../issues) with:

- A clear description of the problem
- Steps to reproduce it
- The expected behaviour vs. what actually happened
- Your Python version and operating system

### Suggesting features

Feature suggestions are welcome via GitHub Issues. Please include:

- The problem you're trying to solve
- How you currently work around it (if applicable)
- Your suggested solution (if you have one)

### Submitting code

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature-name`)
3. Make your changes
4. Add or update tests as needed
5. Run the test suite to ensure everything passes (`pytest`)
6. Commit your changes with a clear message
7. Push to your fork and submit a pull request

### Code style

- Follow PEP 8 for Python code
- Use type hints where practical
- Write docstrings for public functions and classes
- Keep functions focused — one function, one job

### Adding validation rules

If you're adding support for new regulatory templates or frameworks:

- Reference the official regulatory documentation (e.g., EBA taxonomy version)
- Include the rule ID as defined by the regulator
- Write tests that cover both passing and failing cases
- Document any assumptions or interpretations

## Non-code contributions

You don't need to write code to contribute meaningfully:

- **Documentation** — improve explanations, fix typos, add examples
- **Regulatory expertise** — help us interpret rules correctly, suggest priority templates
- **Testing** — try the tool against your own data and report what works and what doesn't
- **Spreading the word** — write about Regtura, present it at meetups, tell your colleagues

## Code of conduct

Be respectful, be constructive, and assume good intentions. We're building something for a professional industry, and our interactions should reflect that.

## Questions?

If you're unsure about anything, open an issue and ask. There are no bad questions, especially when it comes to regulatory nuances.
