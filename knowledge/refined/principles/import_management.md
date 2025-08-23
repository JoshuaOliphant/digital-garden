# Principle: Module-Level Import Management
**Domain**: Python Development
**Type**: Fundamental
**Confidence**: High

## Statement
All imports, especially for exception handlers and module-level decorators, must be declared at the module level to ensure proper scope resolution and avoid runtime errors.

## Rationale
Python's import system and scope resolution work differently for module-level constructs like exception handlers, decorators, and class definitions. These execute in module scope, not function scope, requiring all dependencies to be available at module load time.

## Applications

### Exception Handlers in FastAPI
```python
# ✅ CORRECT: Module-level imports
import uuid
import traceback
from fastapi import HTTPException
from .content_manager import ContentManager

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    error_id = str(uuid.uuid4())[:8]
    # ... handler logic
```

```python
# ❌ INCORRECT: Function-level imports
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    import uuid  # Will cause NameError
    error_id = str(uuid.uuid4())[:8]
```

### Relative Import Strategy
```python
# Project structure awareness
from .models import BaseContent           # Same package
from ..services import ContentService     # Parent package
from app.core import constants           # Absolute from app root
```

## Evidence from Digital Garden

### Instance 1: Exception Handler Imports
- **Problem**: NameError when imports inside exception handler
- **Root Cause**: Exception handlers execute in module scope
- **Solution**: Moved uuid, traceback, ContentManager to module level
- **Result**: Handlers work correctly

### Instance 2: Service Dependencies
- **Pattern**: All service imports at module level
- **Benefit**: Clear dependency graph
- **Result**: No circular import issues

## Best Practices

### 1. Import Organization
```python
# Standard library
import os
import sys
from datetime import datetime

# Third-party packages
import httpx
from fastapi import FastAPI, Request
from pydantic import BaseModel

# Local application
from .models import ContentModel
from .services import ContentService
from .utils import helpers
```

### 2. Lazy Imports (When Necessary)
```python
# For circular dependencies or heavy modules
def process_data():
    from heavy_module import processor  # Only when needed
    return processor.run()
```

### 3. Type Hints and Forward References
```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import User  # Import only for type checking
```

## Common Pitfalls

### ❌ Anti-Pattern: Conditional Module-Level Imports
```python
if DEBUG:
    from debug_toolbar import setup  # May not be available
```

### ✅ Better: Graceful Fallback
```python
try:
    from debug_toolbar import setup
    HAS_DEBUG_TOOLBAR = True
except ImportError:
    HAS_DEBUG_TOOLBAR = False
```

## Testing Implications

```python
# Test files should mirror import structure
# tests/test_main.py
from app.main import app  # Same imports as production
from app.models import BaseContent
```

## Performance Considerations
- Module-level imports happen once at startup
- Function-level imports happen on every call
- Balance between startup time and runtime performance
- Use lazy imports for rarely-used heavy dependencies

## Related Principles
- Dependency Injection
- Separation of Concerns
- Explicit is Better than Implicit

## Checklist
- [ ] All imports at module level by default
- [ ] Exception handler imports at module level
- [ ] Relative imports for package cohesion
- [ ] Organized import sections
- [ ] No circular dependencies
- [ ] Type hints properly handled
- [ ] Test imports mirror production