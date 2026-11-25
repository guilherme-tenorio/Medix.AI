# ADR 0002: MVT com camada de services

- **Status:** Aceito
- **Aprovado em:** 2026-11-25
- **Data:** 2026-11-22

## Contexto

O MEDIX.AI precisa de uma organização comum para implementar os fluxos descritos nas specs. Regras de negócio e consultas ao ORM espalhadas entre Views, Models e outros pontos dificultariam localizar, testar e reutilizar essas regras. O projeto já estabelece o padrão MVT e requer que as Views sejam classes derivadas de `django.views.View`.

## Decisão

- O sistema usa Django seguindo MVT (Model, View, Template), com uma camada de services para concentrar as regras de negócio e todas as consultas ao ORM.
- Toda View é uma classe que herda de `django.views.View` e implementa somente os métodos HTTP necessários; mixins de acesso podem ser usados.
- Views recebem a requisição, validam a entrada de interface quando aplicável, chamam services e convertem o resultado em resposta HTTP ou contexto de Template. Não implementam regras de negócio nem consultas ao ORM.
- Services recebem dados ou objetos de domínio, nunca `request`, e não retornam `HttpResponse`. Eles aplicam as regras de negócio e executam as operações do ORM.
- Models representam os dados persistidos; Templates apresentam os dados preparados pela View e não contêm regras de negócio nem consultas.

## Consequências

- As regras ficam concentradas em uma camada que pode ser chamada por diferentes fluxos e testada sem depender do ciclo HTTP.
- Views mantêm responsabilidade focada em entrada HTTP e resposta, e Models mantêm representação do estado persistido.
- Cada funcionalidade exige contratos explícitos entre View, Form, Service, Model e Template nas specs correspondentes.
- A camada adicional de services introduz mais módulos e chamadas; mudanças no domínio podem exigir atualização coordenada dos services e das Views consumidoras.
- A divisão dos apps por domínio está definida no [ADR 0004](0004-apps-django-por-dominio.md); contratos de services, tratamento de transações e dependências concretas continuam a ser detalhados nas specs aplicáveis.
