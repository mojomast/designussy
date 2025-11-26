# 🍌 DevPlan: LLM-Defined Types & Diversity System

**Project**: NanoBanana (bananajam)  
**Date**: 2025-11-25  
**Status**: Planning Complete

---

## 📋 Executive Summary

Transform NanoBanana from static generators into a dynamic, LLM-driven asset creation platform with three core capabilities:

1. **LLM-Defined Types** - AI creates new generator types at runtime
2. **Dynamic Loading** - Modular, plugin-based type system
3. **Diversity Engine** - Sophisticated variation strategies

---

## 🎯 Goals & Success Metrics

### Technical Goals
- Type creation success rate: >90%
- Generation latency increase: <100ms
- Diversity score target: >0.7
- Test coverage: >85%

### User Experience Goals
- Type creation time: <30 seconds via LLM
- Type reuse rate: >60%
- Variation quality rating: >4/5

---

## 📊 Current State Analysis

### Strengths ✅
- Modular generator architecture (BaseGenerator, registry, factory)
- Advanced parameter system with Pydantic validation
- Metadata & versioning infrastructure
- LLM integration via llm_director.py

### Gaps ❌
- Static type definitions hardcoded in `__init__.py`
- No runtime type creation capability
- Limited variation beyond seed-based randomness
- No dynamic loading mechanism

---

## 🗺️ Implementation Roadmap

### Phase 1: Type System Foundation (Week 1)

**Deliverables:**
- `ElementType` Pydantic model with validation
- `ElementTypeRegistry` for type management
- SQLite persistence layer for types
- Migration script for existing generators

**Key Files:**
- `generators/element_types.py` - Schema definitions
- `generators/type_registry.py` - Registry implementation
- `generators/type_storage.py` - Persistence layer

**Acceptance Criteria:**
- Can register new element types dynamically
- Types persist across restarts
- Backward compatibility maintained

---

### Phase 2: Type-Aware Generators (Week 2)

**Deliverables:**
- Extended `BaseGenerator` with type awareness
- `DynamicGeneratorLoader` for runtime type loading
- Variation strategy framework
- Updated existing generators

**Key Files:**
- `generators/base_generator.py` - Type-aware base class
- `generators/dynamic_loader.py` - Dynamic loading system
- All generator implementations updated

**Acceptance Criteria:**
- Generators can be loaded by type ID
- Variation strategies apply automatically
- Backward compatibility preserved

---

### Phase 3: LLM Type Creation (Week 3)

**Deliverables:**
- `LLMTypeCreator` class for AI-powered type creation
- API endpoints for type management
- Validation and safety mechanisms
- Prompt engineering for better results

**Key Files:**
- `generators/llm_type_creator.py` - LLM integration
- `backend.py` - New API endpoints
- Prompt templates and schemas

**Acceptance Criteria:**
- LLM creates valid types from natural language
- Type validation prevents invalid definitions
- API rate limiting prevents abuse

---

### Phase 4: Diversity & Variation (Week 4)

**Deliverables:**
- `VariationEngine` with multiple strategies
- `DiversityAnalyzer` for metrics
- Configuration UI for variation settings
- Monitoring and reporting

**Key Files:**
- `generators/variation_strategies.py` - Strategy implementations
- `generators/diversity_metrics.py` - Analytics
- Frontend variation config components

**Variation Strategies:**
1. **Jitter** - Small random perturbations
2. **Strategy Pool** - Predefined parameter sets
3. **Seeded** - Deterministic variations
4. **Parameter Sampling** - Distribution-based sampling
5. **Compositional** - Combined strategies

**Acceptance Criteria:**
- Each strategy produces measurably diverse outputs
- Diversity scores tracked and reported
- Strategies configurable via UI

---

### Phase 5: Frontend Integration (Week 5)

**Deliverables:**
- Type browser with search/filter
- LLM type creator UI
- Type-aware asset editor
- Variation configuration interface

**Key Components:**
- `TypeBrowser.jsx` - Browse and search types
- `LLMTypeCreator.jsx` - AI type creation UI
- `TypeAwareAssetEditor.jsx` - Integrated editor
- `VariationConfig.jsx` - Strategy configuration

**Acceptance Criteria:**
- Users can create types via natural language
- Types are browsable and searchable
- Asset generation uses selected types
- Variation strategies configurable in UI

---

### Phase 6: Testing & Documentation (Week 6)

**Deliverables:**
- Comprehensive test suite
- User documentation
- API documentation
- Developer guides

**Test Coverage:**
- Unit tests for all new components
- Integration tests for workflows
- E2E tests for user journeys
- Performance benchmarks

**Documentation:**
- User guide for type creation
- API reference for developers
- Architecture documentation
- Troubleshooting guide

**Acceptance Criteria:**
- Test coverage >85%
- All user flows documented
- API fully documented
- Performance benchmarks met

---

## 🏗️ Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                    ElementType System                    │
├─────────────────────────────────────────────────────────┤
│  ElementType Registry → Type Storage → Dynamic Loader   │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                  Generator System                        │
├─────────────────────────────────────────────────────────┤
│  BaseGenerator → Type-Aware Generators → Variation Engine│
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    LLM Integration                       │
├─────────────────────────────────────────────────────────┤
│  LLMTypeCreator → Prompt Templates → Validation         │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                     Frontend UI                          │
├─────────────────────────────────────────────────────────┤
│  TypeBrowser → LLMCreator → AssetEditor → VariationUI   │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Type Creation**: User prompt → LLM → ElementType → Registry
2. **Asset Generation**: Type ID → Loader → Generator → Variation → Image
3. **Diversity Tracking**: Generation → Analyzer → Metrics → Reports

---

## 🔧 Technical Specifications

### ElementType Schema

```python
class ElementType(BaseModel):
    type_id: str                    # Unique identifier
    name: str                       # Human-readable name
    description: str                # Type description
    category: str                   # Category (backgrounds/glyphs/creatures/ui)
    base_generator: str             # Base generator class
    default_parameters: Dict        # Default parameter values
    variation_strategy: Enum        # Variation strategy type
    variation_config: Dict          # Strategy configuration
    created_by: str                 # Creator identifier
    created_at: datetime            # Creation timestamp
    llm_prompt: Optional[str]       # Original LLM prompt
```

### API Endpoints

**Type Management:**
- `POST /types/create` - Create type with LLM
- `GET /types` - List all types
- `GET /types/{type_id}` - Get specific type
- `PUT /types/{type_id}` - Update type
- `DELETE /types/{type_id}` - Delete type

**Generation:**
- `POST /types/{type_id}/generate` - Generate with type
- `GET /types/{type_id}/preview` - Preview type parameters

**Analytics:**
- `GET /types/{type_id}/diversity` - Get diversity metrics
- `GET /types/{type_id}/usage` - Get usage statistics

---

## 🎨 Variation Strategies

### 1. Jitter Variation
**Purpose**: Small random perturbations for organic variation

**Configuration:**
```python
{
    "jitter_amount": 0.1  # ±10% variation
}
```

**Use Cases**: Subtle variations, natural textures, organic forms

---

### 2. Strategy Pool
**Purpose**: Select from predefined parameter sets

**Configuration:**
```python
{
    "strategy_pool": [
        {"complexity": 30, "chaos": 0.5},
        {"complexity": 70, "chaos": 1.5},
        {"complexity": 50, "chaos": 1.0}
    ]
}
```

**Use Cases**: Distinct styles, mood variations, thematic sets

---

### 3. Seeded Variation
**Purpose**: Deterministic variations for reproducibility

**Configuration:**
```python
{
    "seed": 42,
    "variation_strength": 0.05
}
```

**Use Cases**: Batch generation, consistent variations, debugging

---

### 4. Parameter Sampling
**Purpose**: Sample from probability distributions

**Configuration:**
```python
{
    "distributions": {
        "complexity": {
            "type": "normal",
            "mean": 0.6,
            "std": 0.1
        },
        "chaos": {
            "type": "uniform",
            "min": 0.5,
            "max": 2.0
        }
    }
}
```

**Use Cases**: Exploration, parameter space mapping, A/B testing

---

### 5. Compositional Variation
**Purpose**: Combine multiple strategies

**Configuration:**
```python
{
    "composition": [
        {"strategy": "jitter", "config": {"jitter_amount": 0.1}},
        {"strategy": "seeded", "config": {"seed": 42}}
    ]
}
```

**Use Cases**: Complex variations, multi-level diversity, fine-tuned control

---

## 📈 Diversity Metrics

### Parameter Diversity
Measures variation in parameter space using coefficient of variation.

**Formula**: `CV = σ / μ` for each numeric parameter

**Target**: CV > 0.3 for good diversity

---

### Output Diversity
Measures uniqueness of generated outputs using image hashes.

**Formula**: `Diversity = Unique_Hashes / Total_Generations`

**Target**: Diversity > 0.7 for high variation

---

### Combined Score
Average of parameter and output diversity.

**Target**: Combined score > 0.7

---

## 🚀 Deployment Strategy

### Week-by-Week Rollout

**Week 1**: Deploy type system
- Database migration for type storage
- Registry service startup
- Backward compatibility testing

**Week 2**: Deploy dynamic loading
- Update generators in production
- Test dynamic loader
- Monitor performance impact

**Week 3**: Deploy LLM integration
- Enable type creation API
- Set up rate limiting
- Monitor LLM API costs

**Week 4**: Deploy variation system
- Enable variation strategies
- Deploy diversity analyzer
- Configure monitoring

**Week 5**: Deploy frontend
- Release new UI components
- User training and documentation
- Collect feedback

**Week 6**: Polish and optimize
- Bug fixes from feedback
- Performance optimization
- Final documentation

---

## ⚠️ Risk Mitigation

### Technical Risks

**Risk**: Performance degradation from dynamic loading
**Mitigation**: Implement caching, optimize queries, use connection pooling

**Risk**: Database corruption from concurrent access
**Mitigation**: Transaction rollbacks, regular backups, validation

**Risk**: LLM API failures or rate limits
**Mitigation**: Retry logic, fallback to manual creation, rate limiting

---

### User Experience Risks

**Risk**: Complexity overload for users
**Mitigation**: Progressive disclosure, good defaults, guided workflows

**Risk**: Poor LLM generation quality
**Mitigation**: Better prompts, validation, user editing capabilities

**Risk**: Low adoption of new system
**Mitigation**: Clear benefits, migration tools, training materials

---

### Business Risks

**Risk**: Increased LLM API costs
**Mitigation**: Caching, rate limiting, cost monitoring, usage caps

**Risk**: Maintenance burden increase
**Mitigation**: Comprehensive tests, good documentation, automated monitoring

---

## 📚 Documentation Plan

### User Documentation
- Type creation guide with examples
- Variation strategy explanations
- UI walkthrough and tutorials
- Troubleshooting common issues

### Developer Documentation
- Architecture overview
- API reference
- Extension guide for custom strategies
- Testing guide

### API Documentation
- OpenAPI/Swagger specification
- Request/response examples
- Error handling guide
- Rate limiting information

---

## 🎯 Success Criteria

### Phase 1 Complete When:
- [ ] ElementType schema defined and validated
- [ ] Type registry operational
- [ ] Persistence layer working
- [ ] Unit tests passing

### Phase 2 Complete When:
- [ ] BaseGenerator extended with type awareness
- [ ] Dynamic loader functional
- [ ] All generators updated
- [ ] Integration tests passing

### Phase 3 Complete When:
- [ ] LLMTypeCreator working
- [ ] API endpoints deployed
- [ ] Type creation successful >90% of time
- [ ] E2E tests passing

### Phase 4 Complete When:
- [ ] All variation strategies implemented
- [ ] Diversity analyzer operational
- [ ] Strategies produce diverse outputs
- [ ] Performance benchmarks met

### Phase 5 Complete When:
- [ ] Frontend components deployed
- [ ] User testing successful
- [ ] UI/UX feedback addressed
- [ ] Accessibility standards met

### Phase 6 Complete When:
- [ ] Test coverage >85%
- [ ] Documentation complete
- [ ] Performance optimized
- [ ] Production deployment ready

---

## 🔄 Next Steps

### Immediate Actions (This Week)
1. Review and approve devplan
2. Set up development environment
3. Create project board with tasks
4. Assign ownership for Phase 1

### Stakeholder Review
- Architecture team: Review technical design
- Product team: Review UX/UI plans
- QA team: Review testing strategy
- DevOps: Review deployment plan

### Kickoff Checklist
- [ ] Devplan approved
- [ ] Team assembled
- [ ] Environment ready
- [ ] Tasks created
- [ ] Timeline confirmed

---

**Made with 🍌 and void magic**

*"In the beginning, there was one type. And then the LLM said: Let there be more."*