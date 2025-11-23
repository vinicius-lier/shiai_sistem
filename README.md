# Sistema de Gestão de Competições de Judô

Sistema Django completo para gestão de competições de Judô, replicando a lógica de planilhas Excel com macros VBA.

## Funcionalidades

1. **Cadastro de Atletas** - Inscrição com cálculo automático de classe e categoria
2. **Tabela Oficial de Categorias** - Gestão de categorias por classe, sexo e peso
3. **Inscrição Automática** - Sistema calcula idade, classe e categorias permitidas
4. **Pesagem** - Registro de peso oficial com ajuste automático de categoria
5. **Eliminação Automática** - Elimina atletas por excesso de peso
6. **Geração Automática de Chaves** - Chaves olímpicas, triangular, melhor de 3, etc.
7. **Registro de Resultados** - Registro de vencedores de cada luta
8. **Pódio Automático** - Definição automática de 1º, 2º, 3º e 3º
9. **Pontuação por Academia** - Cálculo automático de pontos
10. **Ranking Final** - Ranking das academias
11. **Relatórios HTML** - Relatórios simples em HTML

## Instalação e Uso

### Requisitos
- Python 3.8+
- Django 5.2+

### Instalação

1. Clone ou baixe o projeto
2. Instale o Django:
```bash
pip install django
```

3. Execute as migrations:
```bash
python manage.py migrate
```

4. Crie um superusuário (opcional, para acessar o admin):
```bash
python manage.py createsuperuser
```

5. Execute o servidor:
```bash
python manage.py runserver
```

6. Acesse o sistema em: http://127.0.0.1:8000/

### Fluxo de Uso

1. **Cadastrar Academias** - Vá em "Academias" e cadastre as academias participantes
2. **Cadastrar Categorias** - Vá em "Categorias" e cadastre todas as categorias oficiais
3. **Cadastrar Atletas** - Vá em "Cadastrar Atleta" e inscreva os atletas
4. **Pesagem** - Vá em "Pesagem", filtre e registre o peso oficial de cada atleta
5. **Gerar Chaves** - Vá em "Chaves" > "Gerar Nova Chave" para cada categoria
6. **Registrar Lutas** - Em cada chave, registre o vencedor de cada luta
7. **Calcular Pontuação** - Após finalizar todas as chaves, calcule a pontuação
8. **Ver Ranking** - Acesse "Ranking" para ver o ranking final das academias
9. **Gerar Relatórios** - Acesse "Relatórios" para ver os relatórios

## Gerar executável (Linux e Windows)

O projeto pode ser empacotado com [PyInstaller](https://pyinstaller.org/) para distribuir um binário simples que já inicia o servidor Django.

1. Crie um ambiente virtual e instale as dependências:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # No Windows use: .venv\\Scripts\\activate
   pip install -r requirements.txt
   pip install pyinstaller
   ```

2. Use o script auxiliar `package_app.py` para gerar o binário. Ele monta automaticamente os parâmetros `--add-data` corretos para Linux/Windows e inclui o banco `db.sqlite3` (se existir) no binário:

   ```bash
   python package_app.py
   ```

   O resultado ficará em `dist/shiai` (Linux/macOS) ou `dist/shiai.exe` (Windows). Execute o arquivo gerado e acesse `http://127.0.0.1:8000/`.

3. Caso prefira executar o PyInstaller manualmente, o script usa a mesma configuração que os comandos abaixo (note o uso de `:` no Linux/macOS e `;` no Windows para `--add-data`):

   - **Linux/macOS**

     ```bash
     pyinstaller --onefile --name shiai \
       --add-data "judocomp:judocomp" \
       --add-data "atletas:atletas" \
       --add-data "categorias_oficiais_judo.json:categorias_oficiais_judo.json" \
       --add-data "db.sqlite3:db.sqlite3" \
       launcher.py
     ```

   - **Windows (PowerShell)**

     ```powershell
     pyinstaller --onefile --name shiai `
       --add-data "judocomp;judocomp" `
       --add-data "atletas;atletas" `
       --add-data "categorias_oficiais_judo.json;categorias_oficiais_judo.json" `
       --add-data "db.sqlite3;db.sqlite3" `
       launcher.py
     ```

   Inclua o `db.sqlite3` apenas se quiser empacotar um banco inicial junto ao executável.

## Resetar dados para uma nova competição

Para limpar lutas, chaves, atletas e pontuações antes de começar um novo evento, use o comando de gerenciamento `reset_competition`:

```bash
python manage.py reset_competition
```

O comando pedirá confirmação (digite `SIM`). Para uso automático (por exemplo, em scripts), utilize a flag `--force`:

```bash
python manage.py reset_competition --force
```

Categorias e academias são preservadas; apenas os dados da competição atual são removidos.

## Estrutura do Projeto

- `atletas/models.py` - Modelos (Academia, Categoria, Atleta, Chave, Luta)
- `atletas/views.py` - Views (funções)
- `atletas/utils.py` - Lógica de negócio (cálculos, geração de chaves)
- `atletas/templates/` - Templates HTML
- `atletas/admin.py` - Configuração do admin Django

## Pontuação

- **1º lugar**: 10 pontos
- **2º lugar**: 7 pontos
- **3º lugar**: 5 pontos (cada)

## Tipos de Chave

- **1 atleta**: Campeão automático
- **2 atletas**: Melhor de 3
- **3 atletas**: Triangular
- **4+ atletas**: Chave olímpica (4, 8, 16, 32)

## Observações

- O sistema não requer autenticação no MVP
- Todos os dados são salvos em SQLite (banco de dados padrão do Django)
- Os relatórios são gerados em HTML simples
- O sistema está pronto para uso em competições reais

