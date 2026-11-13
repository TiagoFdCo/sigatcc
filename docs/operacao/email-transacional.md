# E-mail transacional (Resend) · pacote 6.3 · C5

O SIGATCC envia os convites de banca e de audiência, e o link de acesso do membro externo, por e-mail. Em desenvolvimento os e-mails só aparecem no log do backend. Em homologação e produção, eles saem pelo **SMTP do Resend**, usando o backend SMTP do próprio Django, sem biblioteca nova.

## Como o envio funciona

- O e-mail sai **depois do commit** da operação. Se a operação for desfeita, nada é enviado.
- Se o envio falhar, a operação continua valendo. A falha fica no log do backend e o convite pode ser reenviado pela tela (PF33).
- O log registra o assunto e a quantidade de destinatários, **nunca o endereço** (RNF12).

## Desenvolvimento

Não precisa de nada. Com `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend` (o padrão do `.env.example`), cada e-mail aparece em:

```bash
docker compose logs -f backend
```

## Homologação e produção

### 1. Conta e domínio no Resend (dependência externa)

1. Crie a conta em resend.com com o e-mail da equipe.
2. Em **Domains → Add Domain**, cadastre o domínio de envio (por exemplo `sigatcc.com.br`).
3. O Resend mostra os registros DNS. Cadastre **exatamente os valores que aparecem no painel** no provedor de DNS do domínio:
   - **SPF**: registro `MX` e registro `TXT` no subdomínio indicado pelo painel (normalmente `send`);
   - **DKIM**: registro `TXT` com o nome indicado (normalmente `resend._domainkey`);
   - **DMARC** (recomendado): `TXT` em `_dmarc` com `v=DMARC1; p=none;` para começar.
4. Clique em **Verify**. A propagação do DNS pode levar de minutos a algumas horas.
5. Em **API Keys**, crie uma chave com permissão de envio (*Sending access*) só para esse domínio.

### 2. Variáveis no servidor (`.env`)

```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
RESEND_API_KEY=re_xxxxxxxxxxxxxxxx
DEFAULT_FROM_EMAIL=SIGATCC <nao-responda@sigatcc.com.br>
SIGATCC_FRONTEND_URL=https://homolog.sigatcc.com.br
```

`EMAIL_HOST` (`smtp.resend.com`), `EMAIL_PORT` (`587`), `EMAIL_HOST_USER` (`resend`) e `EMAIL_USE_TLS` (`True`) já têm o valor certo por padrão. O remetente precisa ser do domínio verificado.

Depois de mudar o `.env`, reinicie o backend: `docker compose up -d backend`.

### 3. Teste de envio

```bash
docker compose exec backend python manage.py enviar_email_teste --para seu-email@exemplo.com
```

O e-mail precisa chegar na **caixa de entrada**, não no spam. No Gmail, em "Mostrar original", SPF e DKIM devem aparecer como `PASS`.

### 4. Teste de entrega do RNF07 (≥ 95% em até 5 min)

```bash
docker compose exec backend python manage.py enviar_email_teste --para seu-email@exemplo.com --quantidade 20
```

Confira no painel do Resend (**Emails**) quantos ficaram como *Delivered* e o horário de entrega. Com 20 envios, a meta é pelo menos 19 entregues em até 5 minutos. Anote o resultado no relatório de testes de RNF (pacote 10.5).

## Problemas comuns

| Sintoma | Causa provável |
|---|---|
| `SMTPAuthenticationError` no log | `RESEND_API_KEY` errada ou sem permissão de envio |
| `SMTPSenderRefused` / domínio não verificado | `DEFAULT_FROM_EMAIL` fora do domínio verificado no Resend |
| E-mail cai no spam | SPF ou DKIM ainda não propagados ou com valor diferente do painel |
| Link do e-mail aponta para `localhost` | `SIGATCC_FRONTEND_URL` não configurada no servidor |
