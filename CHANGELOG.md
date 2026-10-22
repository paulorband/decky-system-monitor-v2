# Changelog

Todas as mudanças relevantes deste plugin. Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/);
versões seguem [SemVer](https://semver.org/lang/pt-BR/). As notas de cada release do GitHub são a seção da versão.

## [0.4.0] - 2026-10-22

### Correções
- A verificação de atualizações não esbarra mais em "Limite de requisições do GitHub atingido": o plugin lê um
  pequeno arquivo `release.json` publicado em cada release, fora da API do GitHub (que permite só 60 consultas por
  hora para toda a rede). A API fica só como reserva para releases antigas.

### Observações
- Para chegar a esta versão, quem está na 0.3.0 ou anterior ainda usa a API uma última vez; se aparecer o aviso de
  limite, aguarde o tempo indicado e verifique de novo.

## [0.3.0] - 2026-10-22

### Novidades
- **Voltar para a versão anterior**: antes de cada atualização o plugin guarda a versão instalada; em
  *Atualizações → Voltar para vX* ela é restaurada e o Decky reinicia.
- **Novidades da versão**: antes de instalar, *Novidades da vX* mostra o que muda em um modal navegável pelo controle.
- **Histórico de versões**: todo o changelog do plugin, também em modal.
- Deploy por SSH guarda a versão anterior e ganhou `--rollback` para restaurar pelo computador.

### Observações
- A primeira cópia de rollback feita pelo próprio plugin é criada na atualização **seguinte** a esta versão.

## [0.2.0] - 2026-10-22

### Mudanças
- Versão de teste do fluxo de atualização automática (sem mudanças de funcionalidade).

## [0.1.0] - 2026-10-22

### Novidades
- Painel no Quick Access Menu com CPU, GPU, RAM, bateria, temperaturas, frequências e ventoinhas, com cores e
  gráficos do último minuto.
- Gerenciador de processos em tela cheia: ordenação por nome, CPU e RAM, agrupamento por jogo (AppID da Steam) ou por
  nome, detalhes de cada processo.
- Interface em português do Brasil, inglês e espanhol, seguindo o idioma da Steam.
- Atualização automática pelas releases do GitHub, com canal opcional de builds de teste.
