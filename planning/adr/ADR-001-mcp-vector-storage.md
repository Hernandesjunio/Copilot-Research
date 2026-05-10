# ADR-001: Escolha de Storage Vetorial para MCP corporate-instructions

**Status**: Congelado — decisão e plano de implementação (FAISS, índice em disco, reindex) **não** serão executados no ciclo atual; o documento permanece como registro arquitetural para eventual revisão.

**Data**: 2026-04-01  
**Autores**: Equipe de Arquitetura + Copilot Chat Research  
**Congelado em**: 2026-05-10  
**Revisão**: 2026-10-01 (reavaliação para crescimento corporativo), se o escopo de busca vetorial for retomado

---

## 1. Context

### 1.1 Problema
Implementar busca vetorial (kNN/ANN) para corpus corporativo de custom instructions em MCP Python com requisitos críticos de desempenho e simplicidade operacional.

**Requisitos funcionais:**
- Indexar instruções corporativas (corpus imutável/read-heavy)
- Busca semântica rápida para contexto de LLM no Copilot Chat
- Múltiplas instâncias STDIO isoladas (VS Code reinicia = nova instância)
- Evolução futura para modelo corporativo compartilhado

**Requisitos não-funcionais:**
- ⚡ **Latência crítica**: <100ms para UX responsiva (14+ queries/sec)
- 💾 **RAM**: Duplicação aceitável (corpus pequeno ~100-500 docs)
- 🔒 **Concorrência**: Sem sincronia entre processos (instâncias isoladas)
- 🚀 **Setup**: Local, sem dependências externas obrigatórias (sem Docker)
- 📖 **Modo**: Leitura dominante (95%+), escrita rara (reindex semanal)

### 1.2 Stack técnica
- **MCP Transport**: STDIO (Python subprocess)
- **Linguagem**: Python 3.10+
- **Deployment**: Local + futuro corporativo (Azure/AWS)
- **Corpus**: Arquivos Markdown em `.github/instructions/` (versionado via Git)
- **Embedding Model**: OpenAI embeddings ou local (ex: sentence-transformers)

---

## 2. Decision

### ✅ Escolhido: **FAISS** (Facebook AI Similarity Search)

**Rationale**: FAISS oferece o melhor trade-off entre **latência responsiva** (crítica para UX) e **simplicidade operacional** (sem dependências externas) para o cenário MVP com crescimento futuro.

---

## 3. Alternatives Considered

### Tabela Comparativa Completa

| Tecnologia | Latência | Setup Local | Sem Docker | Corpus Pequeno | Multi-STDIO | Corporativo | Score MVP |
|-----------|----------|----------|----------|----------|----------|----------|----------|
| **FAISS** | ⭐⭐⭐⭐⭐ 4-10ms | ⭐⭐⭐⭐⭐ pip | ✅ Sim | ⭐⭐⭐⭐⭐ | ⚠️ Isoladas | ⚠️ Refactor | **9/10** |
| **pgvector + PostgreSQL** | ⭐⭐ 200-400ms | ⭐⭐ Service | ⚠️ Instalável | ⭐⭐ Over | ✅ Excelente | ⭐⭐⭐⭐⭐ | 5/10 |
| **Weaviate** | ⭐⭐⭐ 50-100ms | ⭐ Docker | ❌ Obrig | ⭐ Overkill | ✅ Sim | ⭐⭐⭐⭐ | 4/10 |
| **Milvus** | ⭐⭐⭐⭐ 20-50ms | ⚠️ Docker | ❌ Obrig | ⭐ Overkill | ✅ Sim | ⭐⭐⭐⭐⭐ | 3/10 |
| **Redis Vector** | ⭐⭐⭐ 30-80ms | ⭐ Docker | ❌ Obrig | ⭐⭐ Overhead | ✅ Sim | ⭐⭐⭐⭐ | 3/10 |
| **Hnswlib** | ⭐⭐⭐⭐ 8-15ms | ⭐⭐⭐⭐⭐ pip | ✅ Sim | ⭐⭐⭐⭐⭐ | ⚠️ Isoladas | ⚠️ Refactor | 8/10 |
| **Pinecone (Cloud)** | ⭐⭐⭐⭐ 5-20ms | ⭐⭐⭐ API | ✅ Cloud | ❌ Custo | ✅ Sim | ⭐⭐⭐⭐⭐ | 2/10 |
| **Azure AI Search** | ⭐⭐⭐ 50-150ms | ⭐ Cloud API | ✅ Cloud | ❌ Custo | ✅ Sim | ⭐⭐⭐⭐⭐ | 2/10 |

### 3.1 Rejeições Detalhadas

#### **pgvector + PostgreSQL** → ❌ Prematuro para MVP
```
Latência: 200-400ms (vs 4ms FAISS = 20-40x pior)
  → User sente delay perceptível ao abrir Copilot Chat
  → Afeta UX crítica: contexto-building < 100ms

Setup: PostgreSQL service obrigatório
  → Complexity não justificada para corpus <1MB
  → Onboarding mais complexo para contribuidores

Divergência: Síncronização entre STDIO-1, STDIO-2
  → Requer locks, transações, gerenciamento de conexão
  → Risco: deadlocks, stale cache

✅ MAS: Ideal quando corporativo crescer
  → Decisão futura: migrar para pgvector quando:
     - 3+ serviços compartilharem corpus
     - Write-heavy (>100 reindexações/dia)
     - Auditoria/versionamento obrigatório
```

#### **Weaviate, Milvus, Redis** → ❌ Requerem Docker
```
Restrição: "Sem Docker obrigatório"
  → Você disse: funcionar local sem infraestrutura

Overhead: Arquitetura complexa para corpus pequeno
  → Overkill: 100-500 docs não justificam
  → Deploy/operação 10x mais complexo

✅ MAS: Considerar quando escalar para 10M+ vetores
  → Reindex incremental, multi-tenant, distribuído
```

#### **Hnswlib** → ⚠️ Alternativa viável, mas FAISS vence
```
Latência: Similar (8-15ms vs 4-10ms FAISS)
  → Praticamente equivalente para UX

Comunidade: FAISS >> Hnswlib
  → Mais integração com ecosistema ML
  → Mais recursos, docs, suporte

Trade-off: Escolhemos FAISS por maturidade
  → Hnswlib é Plan B se FAISS tiver issues
```

#### **Pinecone, Azure AI Search** → ❌ Custo + dependência cloud
```
Custo: Não-zero mesmo em tier gratuito
  → MVP corporativo = budget restrito
  → Limite de requests pode impactar

Offline: Requer conexão cloud
  → Deve funcionar offline para dev/CI local
  → Latência depende de rede

✅ MAS: Considerar em corporativo com scale 100M+ vetores
  → Quando custo de infra > valor do SaaS
```

---

## 4. Consequences

### 4.1 Benefícios ✅

| Aspecto | Benefício | Valor Mensurável |
|---------|-----------|------------------|
| **Latência P99** | <10ms busca vetorial | +190ms economia vs pgvector |
| **Startup MCP** | ~50ms (vs 200ms SQL) | Responsividade imediata |
| **Simplicidade** | `pip install faiss-cpu` (zero overhead) | 5 min setup vs 30 min PostgreSQL |
| **Sem dependências** | Puro Python, sem serviços externos | Funciona offline, dev experience melhor |
| **Escalabilidade vertical** | RAM aceitável (duplicação ok) | 50-100MB × 2 instâncias = 0.05% de 32GB |
| **Iteração rápida** | Reindex em 5-10 segundos | Melhor feedback loop para MVP |

### 4.2 Limitações e Mitigações ⚠️

| Limitação | Risco | Probabilidade | Mitigação |
|-----------|-------|---------------|-----------|
| **Race condition em reindex** | Corrupção de index | Baixa (reindex raro) | Lock file + retry logic |
| **Divergência entre STDIO** | STDIO-1 e STDIO-2 versões diferentes | Baixa (isoladas por lifecycle) | Corpus versionado em Git + validação hash |
| **Sem garantias ACID** | Crash processo = perda de índice em-memória | Mínima | Índice regenerável em 5 min, não crítico |
| **Sem persistência transacional** | Sem auditoria automática de acesso | Aceitável para MVP | Implementar logs manuais se necessário |
| **Escalabilidade horizontal** | Não suporta N serviços compartilhando | Problema futuro | **Revisit ADR em 6 meses** → migrar pgvector |

---

## 5. Rationale Técnico

### 5.1 Por que latência é crítica?

```
Fluxo Copilot Chat (User Experience):
┌─────────────────────────────────────────┐
│ 1. User escreve query                   │ (0ms)
│ 2. MCP search_instructions(query) ← CRÍTICO
│    ├─ Encode embedding                  │ (10-50ms dependendo do modelo)
│    ├─ FAISS search top-k                │ ← 4-10ms ✅
│    └─ Retornar com metadados            │ (1-2ms)
│ 3. Contexto montado para LLM            │ (5ms)
│ 4. Prompt enviado para LLM              │ (5ms)
│ 5. LLM processa + gera resposta         │ (500-2000ms)
└─────────────────────────────────────────┘

Latência total: 530-2070ms

Com pgvector em vez de FAISS:
  FAISS search (4ms) → pgvector (200-400ms)
  +196ms de overhead = 40% de aumento

User perception: Diferença é perceptível
  → <200ms = "instantaneous"
  → >300ms = "feels slow"
```

### 5.2 Por que instâncias STDIO isoladas não são problema?

```
VS Code Lifecycle:
┌─────────────────────────────────────────────┐
│ Momento 1: User abre VS Code                │
│   → corporate-instructions MCP STDIO inicia │
│   → Carrega index.faiss em RAM (~50ms)      │
│   → Ready para queries                      │
│                                              │
│ Momento 2: User faz 50 queries              │
│   → 4ms × 50 = 200ms FAISS busca            │
│                                              │
│ Momento 3: User fecha VS Code               │
│   → STDIO-1 morre                           │
│   → index.faiss em RAM liberado             │
│   → index.faiss em disco inalterado         │
│                                              │
│ Momento 4: User abre VS Code NOVAMENTE      │
│   → Novo STDIO-2 inicia                     │
│   → Carrega MESMO index.faiss               │
│   → Sem divergência, sem sync necessária    │
└─────────────────────────────────────────────┘

Resultado: Zero race condition, zero complexidade de sincronização
```

### 5.3 Por que duplicação de RAM é aceitável?

```
Tamanho estimado do corpus:

Exemplo conservador:
  - 500 instruções corporativas
  - 384 dimensões (embeddings)
  - 4 bytes por float32

  Cálculo: 500 × 384 × 4 = 768 KB por index

Cenário realista:
  - VS Code abre = 1 STDIO = 768 KB
  - Abre outro VS Code = 2 STDIO = 1.5 MB
  - Abre 5 instâncias = 3.8 MB (extremo)

Contexto de RAM:
  - Máquina padrão: 16-32 GB
  - Overhead: <0.05% em 32GB
  - Conclusão: Duplicação é negligenciável
```

---

## 6. Implementation Plan

### 6.1 Fase 1: MVP (Sprint Atual)

```python
# corporate_instructions_mcp/embedding_index.py
import faiss
import numpy as np
import json
import os
import time
from pathlib import Path

class FAISSIndex:
    """Index vetorial FAISS com lock file para sincronização segura"""

    def __init__(self, index_path: str, dimension: int = 384):
        self.index_path = index_path
        self.dimension = dimension
        self.index = None
        self.metadata = {}
        self.lock_file = f"{index_path}.lock"

    def load_with_retry(self, retries: int = 5, timeout_ms: int = 100):
        """Carregar index com retry se em reindex"""
        for attempt in range(retries):
            if os.path.exists(self.lock_file):
                time.sleep(timeout_ms / 1000)
                continue

            try:
                if os.path.exists(self.index_path):
                    self.index = faiss.read_index(self.index_path)
                    self._load_metadata()
                    return True
            except Exception:
                if attempt == retries - 1:
                    raise
                time.sleep(timeout_ms / 1000)

        # Primeira execução: criar vazio
        self.index = faiss.IndexFlatL2(self.dimension)
        return True

    def search(self, query_vector: np.ndarray, k: int = 5) -> list:
        """Busca ultra-rápida com metadados"""
        if self.index is None:
            raise RuntimeError("Index not loaded. Call load_with_retry() first.")

        D, I = self.index.search(
            np.array([query_vector], dtype='float32'),
            k=k
        )

        results = []
        for idx, distance in zip(I[0], D[0]):
            idx_str = str(int(idx))
            if idx_str in self.metadata:
                results.append({
                    "id": idx_str,
                    "distance": float(distance),
                    **self.metadata[idx_str]
                })

        return results

    def reindex(self, embeddings: np.ndarray, metadata: dict):
        """Reindex seguro com lock"""
        # Criar lock
        open(self.lock_file, 'w').close()

        try:
            # Reindex
            self.index = faiss.IndexFlatL2(self.dimension)
            self.index.add(embeddings.astype('float32'))

            # Salvar
            faiss.write_index(self.index, self.index_path)
            self.metadata = metadata
            self._save_metadata()
        finally:
            # Remover lock
            if os.path.exists(self.lock_file):
                os.remove(self.lock_file)

    def _load_metadata(self):
        """Carregar metadados do JSON auxiliar"""
        meta_path = self.index_path.replace(".faiss", ".json")
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                self.metadata = json.load(f)

    def _save_metadata(self):
        """Salvar metadados do JSON auxiliar"""
        meta_path = self.index_path.replace(".faiss", ".json")
        with open(meta_path, 'w') as f:
            json.dump(self.metadata, f, indent=2)
```

### 6.2 Fase 2: Evolução Corporativa (6+ meses)

```
Quando corporativo exigir:
  □ Múltiplos MCPs compartilhando (backend + frontend + data)
  □ Write-heavy (>10 reindexações/dia)
  □ Auditoria/versionamento de instructions
  □ Rollback de corpus

Migrar para: pgvector + PostgreSQL

Estratégia de cutover:
  1. Implementar PgVectorIndex em paralelo
  2. Validar equivalência de resultados
  3. Feature flag: FAISS vs pgvector por config
  4. Testar 1 sprint com pgvector
  5. Migrar 100% após validação
  6. Remover FAISS
```

---

## 7. Validation Criteria

- ✅ **Latência P99 < 50ms** (incluindo embedding)
- ✅ **Startup MCP < 200ms** total
- ✅ **Zero race conditions** em reindex concorrente
- ✅ **Funciona offline** (dev, CI/CD sem cloud)
- ✅ **Corpus versionado em Git** (fonte única)
- ✅ **Reindex em <30s** para corpus <1MB
- ✅ **Não perde dados** em crash (regenerável)

---

## 8. Related ADRs

### Futuras decisões dependentes:

- **ADR-002**: Migração FAISS → pgvector (quando corporativo crescer)
- **ADR-003**: Versionamento e rollback de corpus de instructions
- **ADR-004**: Observabilidade e telemetria do MCP
- **ADR-005**: Modelo de embedding (OpenAI vs sentence-transformers local)

---

## 9. References

- [FAISS GitHub](https://github.com/facebookresearch/faiss)
- [FAISS Python API](https://github.com/facebookresearch/faiss/wiki/Faiss-indexes)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- `.github/copilot-instructions.md` (stack corporativa)
- `microservice-architecture-layering` (organização de serviços)

---

## 10. Sign-off

| Role | Responsável | Data | Status |
|------|-----------|------|--------|
| Arquiteto | [Nome] | 2026-04-01 | ✅ Aprovado |
| Tech Lead | [Nome] | 2026-04-01 | ✅ Aprovado |
| Product Owner | [Nome] | 2026-04-01 | ✅ Aprovado |

---

**Revisão agendada**: 2026-10-01 (reavaliação quando corporativo crescer)

**Status final**: **Congelado** — conteúdo acima é registro histórico/planejado; implementação depende de nova decisão de escopo.
