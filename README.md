# Rumo à Etec

Site de estudo para o Vestibulinho Etec (Centro Paula Souza, SP).

- Trilha diária de 40 questões, misturando Português, Matemática, Ciências e Humanas.
- 690 questões oficiais de 14 provas (2017 a 2026), digitadas, com gabarito oficial e explicação de cada alternativa.
- Questões próprias comentadas, com ilustrações.
- Mascote Sabi com resposta por voz, painel de evolução, projeção de acertos por área e área da família.
- O progresso de cada aluno fica salvo só no próprio aparelho (localStorage).

## Como abrir

O site é estático: basta servir a pasta, por exemplo com `python3 -m http.server` e abrir `http://localhost:8000`.
Também funciona no GitHub Pages (Settings → Pages → branch `main`, pasta `/`).

## Arquivos

- `index.html`: o site.
- `oficiais/banco.json`: provas, gabarito oficial e área de cada questão.
- `oficiais/textos.json`: texto digitado de cada questão.
- `oficiais/explicacoes.json`: explicações das alternativas.
- `oficiais/fig/`: figuras usadas nas questões.
- `dados/proprias.json`: questões próprias.
- `scripts/`: scripts usados para recortar as provas em PDF e montar os arquivos JSON.

As provas e gabaritos são do Centro Paula Souza, disponíveis publicamente em fatweb.s3.amazonaws.com/vestibulinhoetec.
