# Ligar o Mercado Livre (guia para o dono)

O código já está pronto. Falta só você criar o "app" no Mercado Livre e guardar duas senhas no GitHub.
Sem elas, o robô simplesmente pula o Mercado Livre (nada quebra).

## 1. Criar o app
1. Entre em https://developers.mercadolivre.com.br com a sua conta do Mercado Livre.
2. Vá em **Minhas aplicações** e clique em **Criar nova aplicação**.
3. Dê um nome (ex.: "MuquiranaTech"), escolha uma descrição curta e, em "URL de redirecionamento", coloque
   `https://muquiranatech.pages.dev`. Aceite os termos e salve.
4. Abra o app criado e copie o **App ID** (é o `ML_CLIENT_ID`) e a **Chave secreta** (é o `ML_CLIENT_SECRET`).

## 2. Guardar no GitHub
1. No repositório: **Settings → Secrets and variables → Actions → New repository secret**.
2. Crie `ML_CLIENT_ID` com o App ID e `ML_CLIENT_SECRET` com a chave secreta.

## 3. Conferir
Rode o workflow "Coletar preços" (Actions → Run workflow). No log deve aparecer `== Mercado Livre` com as
buscas. Só entram **lojas oficiais** e produtos **novos**.
Nunca cole a chave secreta no código, em conversa ou em arquivo do repositório.
