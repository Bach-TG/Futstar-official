# Contributing to Futstar

First off, thank you for considering contributing to Futstar! It's people like you that make Futstar such a great platform.

## Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct:

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps which reproduce the problem**
- **Provide specific examples to demonstrate the steps**
- **Describe the behavior you observed after following the steps**
- **Explain which behavior you expected to see instead and why**
- **Include screenshots and animated GIFs** if possible

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- **Use a clear and descriptive title**
- **Provide a step-by-step description of the suggested enhancement**
- **Provide specific examples to demonstrate the steps**
- **Describe the current behavior** and **explain which behavior you expected to see instead**
- **Explain why this enhancement would be useful**

### Pull Requests

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code lints
6. Issue that pull request!

## Development Setup

### Prerequisites

- Node.js 18+
- Rust 1.70+
- Solana CLI 1.17+
- Anchor 0.29+
- Python 3.10+

### Setup Steps

1. Clone the repository
```bash
git clone https://github.com/futstar/futstar-momentum-trading.git
cd futstar-momentum-trading
```

2. Install dependencies
```bash
npm install
cd backend && pip install -r requirements.txt
cd ../contracts && anchor build
```

3. Start local development
```bash
# Terminal 1: Start Solana validator
solana-test-validator

# Terminal 2: Deploy contracts
cd contracts && anchor deploy

# Terminal 3: Start backend
cd backend && uvicorn main:app --reload

# Terminal 4: Start frontend
cd frontend && npm run dev
```

## Coding Standards

### TypeScript/JavaScript

- Use ESLint and Prettier
- Follow Airbnb style guide
- Use meaningful variable names
- Add JSDoc comments for functions

### Python

- Follow PEP 8
- Use type hints
- Add docstrings for all functions and classes
- Use Black for formatting

### Rust

- Follow Rust style guidelines
- Use `cargo fmt` and `cargo clippy`
- Write comprehensive tests
- Document public APIs

### Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

Format:
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **build**: Changes that affect the build system or external dependencies
- **ci**: Changes to our CI configuration files and scripts
- **chore**: Other changes that don't modify src or test files

## Testing

### Running Tests

```bash
# Run all tests
npm test

# Run contract tests
cd contracts && anchor test

# Run backend tests
cd backend && pytest

# Run frontend tests
cd frontend && npm test
```

### Writing Tests

- Write unit tests for all new functionality
- Ensure tests are deterministic
- Mock external dependencies
- Aim for >80% code coverage

## Documentation

- Update README.md with details of changes to the interface
- Update ARCHITECTURE.md for significant architectural changes
- Add inline code comments for complex logic
- Update API documentation for endpoint changes

## Review Process

All submissions require review. We use GitHub pull requests for this purpose. Consult [GitHub Help](https://help.github.com/articles/about-pull-requests/) for more information on using pull requests.

### Review Criteria

- Code quality and standards compliance
- Test coverage and quality
- Documentation completeness
- Performance impact
- Security implications
- Compatibility with existing code

## Community

### Discord

Join our Discord server: [discord.gg/futstar](https://discord.gg/futstar)

### Discussions

- Use GitHub Discussions for general questions
- Use GitHub Issues for bugs and feature requests
- Use Discord for real-time chat

## Recognition

Contributors who make significant contributions will be:
- Added to the CONTRIBUTORS.md file
- Mentioned in release notes
- Given special Discord roles
- Eligible for bounties (when available)

## Questions?

Feel free to contact the maintainers:
- Email: dev@futstar.fun
- Discord: @futstar-dev
- Twitter: @Futstarfun

Thank you for contributing to Futstar! 🚀⚽
