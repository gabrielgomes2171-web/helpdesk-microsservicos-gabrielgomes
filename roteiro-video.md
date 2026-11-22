# HelpDesk TI em microsserviços
Gabriel Gomes

*(vídeo sem áudio: as explicações aparecem nestes cartões)*

---

## 1. Arquitetura
- O monólito virou **3 serviços**: Usuários (login), Inventário (equipamentos) e Chamados.
- Cada serviço tem o **seu próprio banco** (SQLite em um volume separado).
- O **API Gateway** é a única entrada (porta 8000) e serve a tela.
- Chamados consulta Usuários e Inventário **por HTTP**, repassando o token, com **timeout de 3 s**.

---

## 2. Tudo subindo com um comando
- `docker compose up --build` sobe gateway + 3 serviços.
- Em `docker compose ps`, **só o gateway** tem porta publicada.

---

## 3. Fluxo completo pela tela
Como **Carla (técnica)**: abrir chamado → atribuir → resolver → fechar.
Tudo passa pelo gateway. As regras de **SLA** e de **transição de status** continuam iguais.

---

## 4. Segurança
- Sem token → **401** (todo serviço confere o token).
- O segredo `JWT_SEGREDO` vem do `.env`, nunca do código.
- **Ana (solicitante)** só vê os próprios chamados; o chamado de outra pessoa responde "não encontrado".

---

## 5. Bancos separados
Cada serviço tem o seu volume e o seu arquivo de banco.
As **chaves estrangeiras entre serviços** deixaram de existir: agora são só ids.

---

## 6. Falha de um serviço
Vou parar o **Inventário**:
- a lista de chamados e de usuários **continua funcionando**;
- abrir chamado **com equipamento** mostra um **erro claro (503)**, sem travar.

---

## 7. O que mudou em relação ao monólito
**Melhor:** cada serviço é publicado e reiniciado sozinho; uma falha não derruba tudo.
**Mais difícil:** agora existe a rede no meio (timeouts e falhas), não há JOIN nem FK entre serviços,
um usuário desativado mantém o acesso até o token expirar, e os testes precisam simular os outros serviços.

---

## 8. Bônus feitos
- Rota de saúde: `GET /saude` no gateway mostra quais serviços estão no ar.
- Testes por serviço rodando no **GitHub Actions** (um job por serviço).
