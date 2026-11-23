# ADR 0001: PostgreSQL como banco de dados relacional

- **Status:** Aceito
- **Data:** 2026-11-21

## Contexto

O MEDIX.AI precisa de persistência relacional para os fluxos de cadastro, triagem, atendimento e prontuário. A pessoa responsável pelo projeto definiu PostgreSQL como banco de dados. A configuração Django usava SQLite; a configuração da aplicação foi alinhada ao PostgreSQL, mas ainda depende de um servidor e variáveis de ambiente válidas para conectar.

## Decisão

O banco de dados relacional do MEDIX.AI é PostgreSQL. Django 6.1 requer PostgreSQL 15 ou superior. A aplicação usa o driver Psycopg 3, fixado no manifesto de dependências.

## Consequências

- A aplicação e os ambientes que a executam passam a depender de PostgreSQL disponível e configurado.
- Migrações, constraints e consultas devem ser verificadas com o PostgreSQL usado pelo projeto.
- O desenvolvimento local e a implantação precisam de um servidor PostgreSQL e credenciais fornecidas por variáveis de ambiente.
- A versão concreta do servidor, hospedagem, backups, recuperação e operação ainda precisam ser definidos; este ADR não escolhe esses detalhes.
