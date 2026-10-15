# Reports Automation

Backend do projeto aplicado de automacao da emissao de certificados de calibracao para a Schulz S.A.

Este README e o ponto de continuidade para os integrantes que assumirao o front-end, os testes de integracao e a documentacao da entrega. Ele deve ser atualizado antes da entrega final, especialmente com as evidencias reais de execucao e o link do repositorio remoto.

## Objetivo da AV3

Construir uma aplicacao web transacional capaz de receber uma planilha operacional `.xlsx`, processar os pontos de ensaio e apresentar um parecer de calibracao.

O backend implementado nesta etapa realiza:

- leitura de planilha `.xlsx` em memoria;
- identificacao de metadados de cliente e tecnico;
- identificacao dinamica da linha de cabecalho de medicoes;
- calculo da media das leituras por ponto;
- calculo do erro sistematico: `media - nominal`;
- comparacao do erro absoluto com o Limite de Erro Admissivel (LEA);
- classificacao por ponto;
- parecer final aprovado somente quando todos os pontos estao dentro da tolerancia.

Nao fazem parte da versao atual: banco de dados, persistencia, geracao de PDF, autenticacao, logging estruturado, containerizacao, processamento `.txt`, desvio padrao e incerteza expandida.

## Estado do Projeto

### Implementado

- [x] Backend Python com FastAPI.
- [x] Processamento somente em memoria.
- [x] Upload validado para extensao `.xlsx`.
- [x] Leitor XLSX isolado na infraestrutura.
- [x] Port `MeasurementReader` para desacoplar o caso de uso do formato de entrada.
- [x] Modelos separados por arquivo em `app/domain/models`.
- [x] Servico `MetrologyProcessorService` em `app/domain/services`.
- [x] Calculos de media, erro, LEA e parecer final.
- [x] Tratamento de erro de validacao da planilha com resposta HTTP `422`.
- [x] Endpoint de saude `GET /health`.
- [x] Testes unitarios do dominio e do leitor XLSX.

### Pendencias para concluir o MVP

- [ ] Integrar o front-end ao endpoint e apresentar uma interface limpa e intuitiva.
- [ ] Executar teste E2E cobrindo front-end, API e arquivo XLSX real.
- [ ] Validar o backend com o `dados.xlsx` oficial e registrar os resultados obtidos.
- [ ] Adicionar cenarios E2E de aprovado, reprovado e arquivo invalido.
- [ ] Definir e registrar o layout final da planilha aceito pelo produto.
- [ ] Adicionar CORS quando a origem do front-end estiver definida.
- [ ] Adicionar logging, observabilidade e tratamento padronizado de erros.
- [ ] Avaliar persistencia, historico e auditoria para uma fase posterior.
- [ ] Avaliar geracao de PDF conforme o escopo final da equipe.
- [ ] Preparar Docker e configuracao de ambiente para a implantacao em nuvem.
- [ ] Atualizar este README com screenshots, evidencias, comandos finais e link do repositorio.

## Arquitetura

O projeto usa um **monolito modular com API REST**, preparado para evoluir para servicos independentes caso o volume e a complexidade justifiquem essa decisao.

```text
Front-end web ou mobile
          |
          v
FastAPI / API REST
          |
Caso de uso ProcessCalibration
          |
Servico de dominio metrologico
          |
Port MeasurementReader ---- Implementacao XlsxMeasurementReader
```

Responsabilidades:

- `app/api`: rotas HTTP e validacao da entrada da API.
- `app/application`: casos de uso e orquestracao.
- `app/domain/models`: modelos e enumeracoes do dominio.
- `app/domain/ports`: contratos que permitem substituir a infraestrutura.
- `app/domain/services`: regras metrologicas sem dependencia de FastAPI ou Excel.
- `app/infrastructure`: adaptadores concretos, atualmente o leitor XLSX.

Essa separacao aplica SOLID de forma pragmatica. O front-end depende somente do contrato HTTP, e o dominio nao depende do framework web ou da biblioteca de Excel. Microsservicos nao sao necessarios para o MVP; a estrutura atual permite separar ingestao, processamento e certificados em fases futuras.

## Estrutura de Pastas

```text
app/
  api/
    routes.py
  application/
    process_calibration.py
  domain/
    models/
      final_opinion_model.py
      measurement_point_model.py
      point_status_model.py
      processed_point_model.py
    ports/
      measurement_reader.py
    services/
      metrology_processor_service.py
  infrastructure/
    xlsx_reader.py
  main.py
tests/
  test_metrology.py
pyproject.toml
README.md
```

## Requisitos

- Windows, Linux ou macOS.
- Python `3.11` ou superior.
- Pip atualizado.
- Planilha de teste `.xlsx`.

## Instalacao Local

No PowerShell, a partir da raiz do repositorio:

```powershell
python --version
python -m pip --version
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

Se a politica do PowerShell impedir a ativacao do ambiente, os comandos podem ser executados diretamente:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m pytest
```

## Executar a API

Com o ambiente virtual ativo:

```powershell
uvicorn app.main:app --reload
```

A API estara disponivel em:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

Teste de saude:

```powershell
curl.exe http://127.0.0.1:8000/health
```

Resposta esperada:

```json
{"status":"ok"}
```

## Contrato da API

### Processar calibracao

```text
POST /api/v1/calibrations/process
Content-Type: multipart/form-data
Campo do arquivo: file
```

Exemplo:

```powershell
curl.exe -X POST http://127.0.0.1:8000/api/v1/calibrations/process -F "file=@dados.xlsx"
```

Resposta de sucesso:

```json
{
  "metadata": {
    "cliente": "Schulz S.A.",
    "tecnico": "Maria"
  },
  "resultados": [
    {
      "parametro": "P1",
      "nominal": 10.0,
      "leituras": [10.1, 10.3],
      "media": 10.2,
      "erro_sistematico": 0.2,
      "lea": 0.2,
      "status": "DENTRO_DA_TOLERANCIA"
    }
  ],
  "parecer_final": "APROVADO"
}
```

Valores possiveis:

- status do ponto: `DENTRO_DA_TOLERANCIA` ou `FORA_DA_TOLERANCIA`;
- parecer final: `APROVADO` ou `REPROVADO`.

Respostas de erro:

- `415`: arquivo diferente de `.xlsx`;
- `422`: planilha vazia, estrutura invalida, coluna obrigatoria ausente ou valor numerico invalido.

## Formato Esperado da Planilha

O leitor procura uma linha contendo uma coluna equivalente a `Parametro` ou `Caracteristica`. A partir dela, procura as colunas:

- parametro: `Parametro` ou `Caracteristica`;
- nominal: `Nominal` ou `Valor Nominal`;
- LEA: `LEA`, `Limite de Erro Admissivel` ou equivalente;
- alternativamente ao LEA, `Tol +` e/ou `Tol -`;
- uma ou mais colunas contendo `Medida`, `Medicao`, `Leitura` ou `Valor Obtido`.

Metadados podem aparecer antes da tabela com rotulos como `Cliente`, `Solicitante`, `Tecnico`, `Executante` ou `Metrologista`.

Para a validacao oficial, usar o `dados.xlsx` fornecido pelo professor e registrar qualquer diferenca entre o formato real e esta documentacao.

## Testes

### Testes unitarios atuais

Os testes atuais verificam o dominio e o leitor XLSX:

```powershell
python -m pytest
```

Resultado validado durante o desenvolvimento: `3 passed`.

### Teste E2E obrigatorio antes da entrega

O teste E2E deve validar a integracao completa entre front-end e backend, e nao apenas chamar o servico de dominio. O fluxo minimo deve ser:

1. iniciar a API;
2. iniciar o front-end;
3. abrir a tela de importacao;
4. selecionar um `.xlsx` real;
5. enviar o arquivo;
6. verificar cliente e tecnico exibidos;
7. verificar media, erro, LEA e status de cada ponto;
8. verificar o parecer final aprovado;
9. repetir com uma planilha que contenha pelo menos um ponto fora da tolerancia;
10. verificar mensagem adequada para arquivo invalido ou extensao nao suportada.

O colega responsavel deve registrar:

- ferramenta usada, por exemplo Playwright;
- comandos de execucao;
- arquivos de entrada;
- resultado de cada cenario;
- screenshots ou videos dos fluxos relevantes;
- logs de falha, quando houver;
- data e ambiente da execucao.

O teste E2E deve ser executado novamente depois de qualquer alteracao no contrato da API ou no layout da planilha.

## Boas Praticas para o MVP

- manter regras de negocio fora das rotas HTTP;
- nao alterar os nomes dos campos do contrato sem alinhar com o front-end;
- validar arquivos e valores antes de processar;
- nao commitar arquivos `.xlsx` com dados sensiveis;
- usar nomes de branch e commits descritivos;
- revisar o README junto com cada mudanca relevante;
- adicionar teste para cada nova regra de negocio;
- manter dependencias no `pyproject.toml`;
- separar configuracoes de ambiente do codigo;
- registrar evidencias reproduziveis para a entrega;
- evitar incluir dados pessoais reais nos exemplos, screenshots e logs.

## Checklist de Entrega

- [ ] API inicia em ambiente limpo seguindo este README.
- [ ] Front-end consome o contrato documentado.
- [ ] Planilha oficial foi processada com sucesso.
- [ ] Cenario aprovado validado.
- [ ] Cenario reprovado validado.
- [ ] Cenario de arquivo invalido validado.
- [ ] Teste E2E executado e evidenciado.
- [ ] Testes unitarios executados sem falhas.
- [ ] README atualizado com os resultados finais.
- [ ] Documentacao do projeto revisada antes da entrega.
- [ ] Link do repositorio remoto incluido no relatorio final.
- [ ] Nenhum segredo, credencial ou dado sensivel foi versionado.
