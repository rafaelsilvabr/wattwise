'use strict';
(() => {
  const core = window.WattWiseMonitor, el = id => document.getElementById(id);
  const format = (value, digits=0) => new Intl.NumberFormat('pt-BR',{maximumFractionDigits:digits,minimumFractionDigits:digits}).format(value);
  const text = value => String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const storageKey = 'wattwise-simulated-connections-v1';
  let connected = new Set(['tv','fridge','ac','shower']);
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey));
    if (Array.isArray(saved)) connected = new Set(saved.filter(id=>core.devices.some(d=>d.id===id)));
  } catch { /* Simulation stays usable without browser storage. */ }
  let room='living', scenario='day', running=true, energy=0, elapsed=0, heldPower=null;
  let lastTime=performance.now(), lastSnapshot, points=[], events=[], pairingTimer=null;
  function persist() { try {localStorage.setItem(storageKey,JSON.stringify([...connected]));} catch {notice('Conexão demo ativa nesta sessão; não foi possível salvá-la neste navegador.');} }
  function notice(message) {el('monitor-notice').textContent=message;}
  function event(message) {
    events.unshift({time:new Date().toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'}),message});
    events=events.slice(0,4);
    el('sensor-events').innerHTML=events.map(e=>`<li><time>${e.time}</time><span>${text(e.message)}</span></li>`).join('');
  }
  function renderSensors() {
    el('selected-room').textContent=core.rooms[room];
    const assigned=core.devices.filter(d=>d.room===room), online=assigned.filter(d=>connected.has(d.id)).length;
    el('room-description').textContent=`${online} de ${assigned.length} sensores demo conectados neste ambiente.`;
    el('room-sensors').innerHTML=assigned.map(d=>`<article class="sensor-card"><div class="sensor-card-title"><span class="sensor-mini-icon">⌁</span><div><strong>${text(d.name)}</strong><small>${text(d.kind)}</small></div><span class="sensor-state ${connected.has(d.id)?'connected':''}">${connected.has(d.id)?'Demo online':'Desconectado'}</span></div><div class="sensor-reading-row"><strong id="sensor-reading-${d.id}">—</strong><button class="text-button" data-sensor-id="${d.id}" data-sensor-action="${connected.has(d.id)?'disconnect':'connect'}">${connected.has(d.id)?'Desconectar demo':'Conectar demo ↗'}</button></div></article>`).join('');
    document.querySelectorAll('[data-room]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.room===room)));
    document.querySelectorAll('[data-floor]').forEach(f=>f.classList.toggle('selected',f.dataset.floor===room));
  }
  function paint(reading, appendPoint) {
    el('monitor-power').textContent=reading.watts===null?'—':`${format(reading.watts)} W`;
    el('monitor-energy').textContent=`${format(energy,5)} kWh`;
    el('monitor-live').textContent=running&&!document.hidden?`● Simulação · ${reading.online} sensores conectados`:'Ⅱ Simulação em pausa';
    el('monitor-live').classList.toggle('paused',!running||document.hidden);
    for (const [id,r] of Object.entries(reading.rooms)) {
      const marker=document.querySelector(`[data-room-power="${id}"]`);
      marker.textContent=r.connected?`${format(r.watts)} W`:'Sem leitura';
      marker.parentElement.classList.toggle('has-reading',r.connected>0);
    }
    for (const sensor of reading.readings) {
      const value=el(`sensor-reading-${sensor.id}`);
      if (value) value.textContent=sensor.watts===null?'—':`${format(sensor.watts)} W`;
    }
    if (appendPoint) {
      // Disconnection is a gap, never an invented zero-watt reading.
      if (reading.watts===null) points=[];
      else points=[...points,reading.watts].slice(-40);
      const max=Math.max(100,...points);
      const coordinates=points.map((w,i)=>`${i*600/Math.max(1,points.length-1)},${68-w/max*58}`);
      el('sparkline-line').setAttribute('points',coordinates.join(' '));
      el('sparkline-fill').setAttribute('d',coordinates.length>1?`M0,76 L${coordinates.join(' L')} L600,76 Z`:'');
      el('monitor-updated').textContent=`Simulado às ${new Date().toLocaleTimeString('pt-BR')}`;
    }
  }
  function tick(appendPoint=true) {
    const now=performance.now(), delta=Math.max(0,Math.min((now-lastTime)/1000,5));
    lastTime=now;
    if (!running||document.hidden) {heldPower=null; if(lastSnapshot)paint(lastSnapshot,false); return;}
    energy=core.integrate(energy,heldPower,delta); elapsed+=delta;
    lastSnapshot=core.snapshot(connected,scenario,elapsed); heldPower=lastSnapshot.watts;
    paint(lastSnapshot,appendPoint);
  }
  function chooseRoom(id) {room=id;renderSensors();if(lastSnapshot)paint(lastSnapshot,false);}
  function openConnection(id) {
    const available=core.devices.filter(d=>!connected.has(d.id));
    el('demo-device').innerHTML=available.map(d=>`<option value="${d.id}">${text(d.name)} · ${text(core.rooms[d.room])}</option>`).join('');
    el('demo-device').disabled=!available.length; el('pair-demo').disabled=!available.length;
    if(id&&available.some(d=>d.id===id))el('demo-device').value=id;
    preview(); el('connect-dialog').showModal();
  }
  function preview() {
    const device=core.devices.find(d=>d.id===el('demo-device').value);
    el('connect-preview').textContent=device?`O sensor será exibido em ${core.rooms[device.room]}. Este pareamento e seus valores são simulados.`:'Todos os sensores da demonstração já estão conectados. Você pode desconectar um para repetir o fluxo.';
  }
  el('demo-device').onchange=preview;
  el('connect-demo-device').onclick=()=>openConnection();
  el('close-connect').onclick=()=>el('connect-dialog').close();
  el('connect-dialog').addEventListener('close',()=>{clearTimeout(pairingTimer);pairingTimer=null;el('pair-demo').textContent='Simular conexão';el('pair-demo').disabled=false;});
  el('connect-form').onsubmit=e=>{
    e.preventDefault(); const device=core.devices.find(d=>d.id===el('demo-device').value);
    if(!device||pairingTimer)return;
    el('pair-demo').disabled=true;el('pair-demo').textContent='Simulando pareamento…';
    pairingTimer=setTimeout(()=>{
      tick(false); connected.add(device.id); persist(); chooseRoom(device.room);tick();
      event(`${device.name}: conexão demo adicionada`);notice(`${device.name} conectado ao simulador. Nenhum dispositivo real foi pareado.`);
      el('connect-dialog').close();
    },650);
  };
  el('room-sensors').onclick=e=>{
    const button=e.target.closest('[data-sensor-id]');if(!button)return;
    const device=core.devices.find(d=>d.id===button.dataset.sensorId);if(!device)return;
    if(button.dataset.sensorAction==='connect')return openConnection(device.id);
    tick(false);connected.delete(device.id);persist();renderSensors();tick();
    event(`${device.name}: sensor demo desconectado`);notice(`${device.name}: leitura indisponível após desconexão do sensor demo.`);
  };
  document.querySelectorAll('[data-room]').forEach(button=>button.onclick=()=>chooseRoom(button.dataset.room));
  el('monitor-scenario').onchange=()=>{
    tick(false);scenario=el('monitor-scenario').value;tick();
    event(`Cenário: ${el('monitor-scenario').selectedOptions[0].textContent}`);
    notice('Cenário alterado somente no simulador. Nenhum aparelho real foi controlado.');
  };
  el('pause-monitor').onclick=()=>{
    tick(false);running=!running;lastTime=performance.now();heldPower=null;
    el('pause-monitor').textContent=running?'Ⅱ Pausar simulação':'▷ Retomar simulação';
    event(running?'Simulação retomada':'Simulação pausada');tick(false);
  };
  document.addEventListener('visibilitychange',()=>{lastTime=performance.now();heldPower=null;tick(false);});
  renderSensors();event('Casa demonstrativa pronta · leituras fictícias');tick();setInterval(tick,3000);
})();
