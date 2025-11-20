"""
Serviços para atualização de lutas e avanço de vencedores/perdedores.
Implementa lógica idempotente de atualização de chaves.
"""
from django.db import transaction
from django.db.models import Max
from atletas.models import Luta, Chave, Atleta, AdminLog


@transaction.atomic
def atualizar_vencedor_luta(luta, vencedor, tipo_vitoria='IPPON', wo_atleta_a=False, wo_atleta_b=False):
    """
    Atualiza o vencedor de uma luta e avança automaticamente para próxima luta.
    Lógica idempotente: pode ser chamada múltiplas vezes sem duplicar.
    """
    if luta.concluida and luta.vencedor == vencedor:
        # Já está atualizado, não fazer nada
        return luta
    
    # Determinar perdedor
    perdedor = None
    if luta.atleta_a and luta.atleta_a.id == vencedor.id:
        perdedor = luta.atleta_b
    elif luta.atleta_b and luta.atleta_b.id == vencedor.id:
        perdedor = luta.atleta_a
    
    # Atualizar luta
    luta.vencedor = vencedor
    luta.perdedor = perdedor
    luta.tipo_vitoria = tipo_vitoria
    luta.wo_atleta_a = wo_atleta_a
    luta.wo_atleta_b = wo_atleta_b
    luta.concluida = True
    
    # Calcular pontos conforme tipo de vitória
    if tipo_vitoria == "IPPON":
        luta.pontos_vencedor = 10
        luta.ippon_count = 1
        luta.wazari_count = 0
        luta.yuko_count = 0
    elif tipo_vitoria in ["WAZARI", "WAZARI_WAZARI"]:
        luta.pontos_vencedor = 7
        luta.ippon_count = 0
        luta.wazari_count = 1
        luta.yuko_count = 0
    elif tipo_vitoria == "YUKO":
        luta.pontos_vencedor = 1
        luta.ippon_count = 0
        luta.wazari_count = 0
        luta.yuko_count = 1
    elif tipo_vitoria == "WO":
        luta.pontos_vencedor = 10  # WO conta como Ippon
        luta.ippon_count = 0
        luta.wazari_count = 0
        luta.yuko_count = 0
    
    luta.pontos_perdedor = 0
    luta.save()
    
    # Avançar vencedor para próxima luta (se houver)
    if luta.proxima_luta:
        proxima = luta.proxima_luta
        if proxima.atleta_a is None:
            proxima.atleta_a = vencedor
        elif proxima.atleta_b is None:
            proxima.atleta_b = vencedor
        proxima.save()
    
    # Avançar perdedor para repescagem (se houver)
    if perdedor and luta.proxima_luta_repescagem:
        repescagem = luta.proxima_luta_repescagem
        if repescagem.atleta_a is None:
            repescagem.atleta_a = perdedor
        elif repescagem.atleta_b is None:
            repescagem.atleta_b = perdedor
        repescagem.save()
    
    # ✅ NOVO: Lógica especial para eliminatória simples com 3 atletas (stand-by)
    if luta.chave and luta.chave.tipo_chave == 'SIMPLES_3' and luta.round == 1:
        # Quando a luta 1 termina, o vencedor vai para a luta 2 (final) como atleta_b
        if vencedor and luta.proxima_luta:
            luta2 = luta.proxima_luta
            if luta2.round == 2 and luta2.atleta_b is None:
                luta2.atleta_b = vencedor
                luta2.save()
    
    # ✅ CORREÇÃO: Lógica especial para chave casada 3 - perdedor avança para luta2
    if luta.chave and luta.chave.tipo_chave == 'CASADA_3' and luta.round == 1:
        # Para chave casada, o perdedor da luta 1 vai para luta 2 (atleta_b)
        if perdedor and luta.proxima_luta:
            proxima = luta.proxima_luta
            # Verificar se é a luta 2 (round 2) e se atleta_b está vazio
            if proxima.round == 2 and proxima.atleta_b is None:
                proxima.atleta_b = perdedor
                proxima.save()
        
        # Vencedor da luta 1 avança para final (luta 3) como atleta_a
        if vencedor and luta.proxima_luta and luta.proxima_luta.proxima_luta:
            final = luta.proxima_luta.proxima_luta
            if final.round == 3 and final.atleta_a is None:
                final.atleta_a = vencedor
                final.save()
    
    return luta


@transaction.atomic
def recalcular_chave(chave):
    """
    Recalcula toda a chave baseado nas lutas concluídas.
    Atualiza automaticamente próximas lutas e repescagens.
    Lógica idempotente.
    """
    # Buscar todas as lutas concluídas ordenadas por round
    lutas_concluidas = chave.lutas.filter(concluida=True, vencedor__isnull=False).order_by('round', 'id')
    
    for luta in lutas_concluidas:
        vencedor = luta.vencedor
        perdedor = luta.get_perdedor()
        
        # Lógica especial para chave casada 3
        if chave.tipo_chave == 'CASADA_3':
            if luta.round == 1:
                # Luta 1: perdedor vai para luta 2 (atleta_b), vencedor vai para final (atleta_a)
                if luta.proxima_luta:  # Luta 2
                    luta2 = luta.proxima_luta
                    if perdedor and luta2.atleta_b is None:
                        luta2.atleta_b = perdedor
                        luta2.save()
                    
                    # Vencedor da luta 1 vai para final
                    if luta2.proxima_luta and vencedor:  # Final (luta 3)
                        final = luta2.proxima_luta
                        if final.atleta_a is None:
                            final.atleta_a = vencedor
                            final.save()
            
            elif luta.round == 2:
                # Luta 2: vencedor vai para final (atleta_b)
                if luta.proxima_luta and vencedor:  # Final (luta 3)
                    final = luta.proxima_luta
                    if final.atleta_b is None:
                        final.atleta_b = vencedor
                        final.save()
        
        else:
            # Lógica padrão para outros tipos de chave
            # Avançar vencedor para próxima luta
            if luta.proxima_luta and vencedor:
                proxima = luta.proxima_luta
                if proxima.atleta_a is None:
                    proxima.atleta_a = vencedor
                elif proxima.atleta_b is None and proxima.atleta_a != vencedor:
                    proxima.atleta_b = vencedor
                proxima.save()
            
            # Avançar perdedor para repescagem
            if perdedor and luta.proxima_luta_repescagem:
                repescagem = luta.proxima_luta_repescagem
                if repescagem.atleta_a is None:
                    repescagem.atleta_a = perdedor
                elif repescagem.atleta_b is None and repescagem.atleta_a != perdedor:
                    repescagem.atleta_b = perdedor
                repescagem.save()
    
    return chave


def obter_resultados_chave(chave):
    """
    Retorna os resultados finais da chave: [1º, 2º, 3º, 3º]
    """
    estrutura = chave.estrutura
    tipo_chave = chave.tipo_chave or estrutura.get("tipo", "")
    
    # Melhor de 3
    if tipo_chave == 'MELHOR_DE_3' or estrutura.get("tipo") == "melhor_de_3":
        lutas = chave.lutas.filter(round=1).order_by('id')
        vitorias = {}
        atletas_ids = set()
        
        for luta in lutas:
            if luta.atleta_a:
                atletas_ids.add(luta.atleta_a.id)
            if luta.atleta_b:
                atletas_ids.add(luta.atleta_b.id)
            
            if luta.vencedor and luta.concluida and luta.tipo_vitoria != "YUKO":
                vencedor_id = luta.vencedor.id
                vitorias[vencedor_id] = vitorias.get(vencedor_id, 0) + 1
        
        # Verificar se algum atleta atingiu 2 vitórias
        vencedor_id = None
        for atleta_id, num_vitorias in vitorias.items():
            if num_vitorias >= 2:
                vencedor_id = atleta_id
                break
        
        if vencedor_id:
            perdedor_id = None
            for atleta_id in atletas_ids:
                if atleta_id != vencedor_id:
                    perdedor_id = atleta_id
                    break
            return [vencedor_id, perdedor_id]
        return []
    
    # ✅ NOVO: Eliminatória simples com 3 atletas (stand-by)
    if tipo_chave == 'SIMPLES_3' or estrutura.get("tipo") == "simples_3":
        # Buscar luta final (round 2)
        final = chave.lutas.filter(round=2, tipo_luta='FINAL').first()
        if final and final.vencedor and final.concluida:
            vencedor_id = final.vencedor.id
            perdedor_id = final.get_perdedor().id if final.get_perdedor() else None
            
            # Buscar perdedor da luta 1 (round 1) - terceiro lugar
            luta1 = chave.lutas.filter(round=1).first()
            terceiro_id = None
            if luta1 and luta1.get_perdedor():
                terceiro_id = luta1.get_perdedor().id
            
            resultado = [vencedor_id]
            if perdedor_id:
                resultado.append(perdedor_id)
            if terceiro_id:
                resultado.append(terceiro_id)
            return resultado
        return []
    
    # Casada 3
    if tipo_chave == 'CASADA_3' or estrutura.get("tipo") == "casada_3":
        # Buscar luta final (round 3)
        final = chave.lutas.filter(round=3, tipo_luta='FINAL').first()
        if final and final.vencedor:
            vencedor_id = final.vencedor.id
            perdedor_id = final.get_perdedor().id if final.get_perdedor() else None
            
            # Buscar terceiro lugar (perdedor da semifinal que não chegou na final)
            semi = chave.lutas.filter(round=2).first()
            terceiro_id = None
            if semi and semi.vencedor:
                # O perdedor da semifinal que não perdeu para o vencedor da final
                if semi.get_perdedor():
                    terceiro_id = semi.get_perdedor().id
            
            resultado = [vencedor_id]
            if perdedor_id:
                resultado.append(perdedor_id)
            if terceiro_id:
                resultado.append(terceiro_id)
            return resultado
        return []
    
    # Rodízio
    if tipo_chave == 'RODIZIO' or estrutura.get("tipo") == "rodizio":
        lutas = chave.lutas.filter(round=1)
        vitorias = {}
        atletas_ids = set()
        
        for luta in lutas:
            if luta.atleta_a:
                atletas_ids.add(luta.atleta_a.id)
            if luta.atleta_b:
                atletas_ids.add(luta.atleta_b.id)
            
            if luta.vencedor and luta.concluida:
                vencedor_id = luta.vencedor.id
                vitorias[vencedor_id] = vitorias.get(vencedor_id, 0) + 1
        
        # Ordenar por número de vitórias
        ranking = sorted(vitorias.items(), key=lambda x: x[1], reverse=True)
        
        resultado = []
        for atleta_id, num_vitorias in ranking[:3]:
            resultado.append(atleta_id)
        
        return resultado
    
    # Eliminatória simples ou com repescagem
    if tipo_chave in ['ELIMINATORIA_SIMPLES', 'ELIMINATORIA_REPESCAGEM', 'OLIMPICA']:
        # Buscar luta final
        final = chave.lutas.filter(tipo_luta='FINAL').first()
        if not final:
            # Tentar buscar última luta do último round
            ultimo_round = chave.lutas.aggregate(max_round=Max('round'))['max_round']
            if ultimo_round:
                final = chave.lutas.filter(round=ultimo_round).first()
        
        if final and final.vencedor:
            vencedor_id = final.vencedor.id
            perdedor_id = final.get_perdedor().id if final.get_perdedor() else None
            
            resultado = [vencedor_id]
            if perdedor_id:
                resultado.append(perdedor_id)
            
            # Buscar bronze (repescagem)
            if tipo_chave in ['ELIMINATORIA_REPESCAGEM', 'OLIMPICA']:
                bronze = chave.lutas.filter(tipo_luta='BRONZE').first()
                if bronze and bronze.vencedor:
                    resultado.append(bronze.vencedor.id)
                    # Segundo bronze (perdedor da luta de bronze)
                    if bronze.get_perdedor():
                        resultado.append(bronze.get_perdedor().id)
            
            return resultado
        return []
    
    # Liga
    if tipo_chave == 'LIGA':
        # Buscar final
        final = chave.lutas.filter(tipo_luta='FINAL').first()
        if final and final.vencedor:
            vencedor_id = final.vencedor.id
            perdedor_id = final.get_perdedor().id if final.get_perdedor() else None
            
            # Buscar perdedores das semifinais para bronze
            semis = chave.lutas.filter(round=2, tipo_luta='NORMAL')
            terceiros = []
            for semi in semis:
                if semi.get_perdedor() and semi.get_perdedor().id not in [vencedor_id, perdedor_id]:
                    terceiros.append(semi.get_perdedor().id)
            
            resultado = [vencedor_id]
            if perdedor_id:
                resultado.append(perdedor_id)
            resultado.extend(terceiros[:2])  # Máximo 2 terceiros
            
            return resultado
        return []
    
    # Grupos
    if tipo_chave == 'GRUPOS':
        # Lógica simplificada: buscar vencedores dos grupos
        # (implementação completa requer cálculo de pontuação por grupo)
        return []
    
    return []


@transaction.atomic
def finalizar_chave(chave):
    """
    Finaliza a chave e calcula pontos para ranking.
    """
    # Verificar se já foi finalizada
    if chave.finalizada:
        return chave  # Já finalizada, não processar novamente
    
    # Recalcular chave antes de finalizar
    recalcular_chave(chave)
    
    # Obter resultados
    resultados = obter_resultados_chave(chave)
    
    # Atualizar estrutura com resultados
    estrutura = chave.estrutura
    estrutura["resultados"] = resultados
    estrutura["finalizada"] = True
    
    chave.estrutura = estrutura
    chave.finalizada = True
    chave.save()
    
    # Atualizar pontos no EventoAtleta (se houver evento)
    if chave.evento:
        from eventos.models import EventoAtleta
        from atletas.models import AdminLog, Atleta
        
        # Obter parâmetros do evento
        try:
            parametros = chave.evento.parametros
            pontos_1 = parametros.pontuacao_primeiro
            pontos_2 = parametros.pontuacao_segundo
            pontos_3 = parametros.pontuacao_terceiro
        except:
            pontos_1 = 10
            pontos_2 = 7
            pontos_3 = 5
        
        # Atribuir pontos
        for posicao, atleta_id in enumerate(resultados[:5], 1):
            try:
                atleta = Atleta.objects.get(id=atleta_id)
                evento_atleta = EventoAtleta.objects.get(evento=chave.evento, atleta=atleta)
                
                pontos = 0
                if posicao == 1:
                    pontos = pontos_1
                elif posicao == 2:
                    pontos = pontos_2
                elif posicao == 3:
                    pontos = pontos_3
                
                evento_atleta.pontos = (evento_atleta.pontos or 0) + pontos
                evento_atleta.pontos_evento = evento_atleta.pontos
                evento_atleta.save()
                
                # Log
                AdminLog.objects.create(
                    tipo='OUTRO',
                    acao=f'Pontos atribuídos - {atleta.nome}',
                    atleta=atleta,
                    academia=atleta.academia,
                    detalhes=f'Evento: {chave.evento.nome} - Categoria: {chave.categoria} - Posição: {posicao}º - Pontos: {pontos}'
                )
            except (Atleta.DoesNotExist, EventoAtleta.DoesNotExist):
                continue
    
    return chave

