// API基础URL配置
// 动态获取API基础URL，支持远程访问
const API_BASE_URL = (() => {
    // 如果是localhost访问，使用localhost
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return 'http://localhost:5000';
    }
    // 否则使用相同的主机名，但端口改为5000
    return `http://${window.location.hostname}:5000`;
})();

// 全局变量存储当前登录的用户名和会话令牌
let currentLoggedInUser = '';
let sessionToken = '';
let availableCharacters = [];
let currentInventoryData = null; // 存储当前背包数据
let allItemsData = null; // 缓存所有物品数据

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// 获取带认证头的请求配置
function getAuthHeaders() {
    return {
        'Content-Type': 'application/json',
        'X-Session-Token': sessionToken
    };
}

// 发送认证请求的通用函数
async function makeAuthenticatedRequest(url, options = {}) {
    const defaultOptions = {
        headers: getAuthHeaders()
    };
    
    const mergedOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...(options.headers || {})
        }
    };
    
    const response = await fetch(url, mergedOptions);
    
    if (response.status === 401) {
        // 会话过期，重新登录
        await logout();
        return null;
    }
    
    return response;
}

// 初始化应用
async function initializeApp() {
    // 尝试从localStorage恢复会话
    const savedToken = localStorage.getItem('sessionToken');
    const savedUsername = localStorage.getItem('currentUser');
    
    if (savedToken && savedUsername) {
        sessionToken = savedToken;
        currentLoggedInUser = savedUsername;
        
        // 验证会话是否有效
        const isValid = await validateSession();
        if (isValid) {
            document.getElementById('username').value = savedUsername;
            document.getElementById('currentUserDisplay').textContent = savedUsername;
            document.getElementById('usernameDisplay').textContent = savedUsername;
            document.getElementById('loginModal').style.display = 'none';
            document.getElementById('mainContainer').classList.remove('hidden');
            await loadUserData();
            await loadCharacterHistory('龙与地下城');
            changeCharacterImage('龙与地下城');
            document.getElementById('messageInput').focus();
            // 检查当前位置并显示相应的内容
            await checkAndShowLocationContent();
        } else {
            // 会话无效，清除存储的信息
            await logout();
        }
    } else {
        // 否则显示登录界面
        document.getElementById('loginUsername').focus();
    }
    
    // 添加Enter键支持
    document.getElementById('loginUsername').addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            document.getElementById('loginPassword').focus();
        }
    });
    
    document.getElementById('loginPassword').addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            loginUser();
        }
    });
    
    // 加载可用角色列表
    await loadCharacters();
}

// 验证会话
async function validateSession() {
    try {
        const response = await fetch(`${API_BASE_URL}/validate_session`, {
            method: 'POST',
            headers: getAuthHeaders()
        });
        
        const data = await response.json();
        return data.success;
    } catch (error) {
        console.error('验证会话出错:', error);
        return false;
    }
}

// 用户登录
async function loginUser() {
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value.trim();
    
    if (!username || !password) {
        showMessage('请输入用户名和密码', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // 保存会话信息
            currentLoggedInUser = username;
            sessionToken = data.session_token;
            
            // 保存到localStorage
            localStorage.setItem('currentUser', username);
            localStorage.setItem('sessionToken', sessionToken);
            
            // 更新界面
            document.getElementById('username').value = username;
            document.getElementById('currentUserDisplay').textContent = username;
            document.getElementById('usernameDisplay').textContent = username;
            document.getElementById('loginModal').style.display = 'none';
            document.getElementById('mainContainer').classList.remove('hidden');
            
            // 清空登录表单
            document.getElementById('loginUsername').value = '';
            document.getElementById('loginPassword').value = '';
            
            // 加载用户数据和聊天历史
            await loadUserData();
            await loadCharacterHistory('龙与地下城');
            changeCharacterImage('龙与地下城');
            
            document.getElementById('messageInput').focus();
            showMessage('登录成功！', 'success');
            
            // 确保初始显示默认内容
            showDefaultContent();
        } else {
            showMessage(data.error || '登录失败', 'error');
        }
    } catch (error) {
        showMessage('登录请求失败: ' + error.message, 'error');
    }
}

// 用户注册
async function registerUser() {
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value.trim();
    
    if (!username || !password) {
        showMessage('请输入用户名和密码', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('注册成功！请登录', 'success');
        } else {
            showMessage(data.error || '注册失败', 'error');
        }
    } catch (error) {
        showMessage('注册请求失败: ' + error.message, 'error');
    }
}

// 用户登出
async function logout() {
    try {
        if (sessionToken) {
            await fetch(`${API_BASE_URL}/logout`, {
                method: 'POST',
                headers: getAuthHeaders()
            });
        }
    } catch (error) {
        console.error('登出请求出错:', error);
    }
    
    // 清除会话信息
    currentLoggedInUser = '';
    sessionToken = '';
    localStorage.removeItem('currentUser');
    localStorage.removeItem('sessionToken');
    
    // 重置界面
    document.getElementById('loginModal').style.display = 'block';
    document.getElementById('mainContainer').classList.add('hidden');
    document.getElementById('loginUsername').focus();
    
    showMessage('已登出', 'info');
}

// 显示消息提示
function showMessage(message, type = 'info') {
    // 创建消息元素
    const messageDiv = document.createElement('div');
    messageDiv.className = `message-toast message-${type}`;
    messageDiv.textContent = message;
    
    // 添加到页面
    document.body.appendChild(messageDiv);
    
    // 3秒后自动消失
    setTimeout(() => {
        messageDiv.remove();
    }, 3000);
}

// 加载角色列表
async function loadCharacters() {
    try {
        const response = await fetch(`${API_BASE_URL}/get_characters`);
        const data = await response.json();
        
        if (data.success) {
            availableCharacters = data.characters;
            updateCharacterSelect();
        }
    } catch (error) {
        console.error('加载角色列表出错:', error);
    }
}

// 更新角色选择框
function updateCharacterSelect() {
    const select = document.getElementById('characterSelect');
    select.innerHTML = '';
    
    Object.keys(availableCharacters).forEach(character => {
        const option = document.createElement('option');
        option.value = character;
        option.textContent = character;
        select.appendChild(option);
    });
}

// 发送聊天消息
async function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (!message) return;
    
    const currentCharacter = document.getElementById('characterSelect').value;
    
    // 添加用户消息到聊天窗口
    addMessageToChat(currentLoggedInUser, message, 'user');
    
    // 普通聊天消息不发送到房间，只与AI对话
    // 只有通过互动按钮发送的消息才会被其他玩家看到
    
    // 清空输入框并显示发送状态
    messageInput.value = '';
    showTypingIndicator();
    
    try {
        const response = await makeAuthenticatedRequest(`${API_BASE_URL}/chat`, {
            method: 'POST',
            body: JSON.stringify({
                message: message,
                character: currentCharacter,
                language: '中文'
            })
        });
        
        if (!response) return; // 认证失败已处理
        
        const data = await response.json();
        
        if (data.success) {
            // 添加AI回复到聊天窗口
            addMessageToChat(currentCharacter, data.reply, 'assistant');
            
            // 在联机模式下，AI回复只在本地显示，不发送到房间
            // if (isMultiplayerMode && currentRoomId) {
            //     sendToRoom(currentCharacter, data.reply, 'global');
            // }
            
            // 解析并处理数值变化
            parseAndUpdateStats(data.reply);
            
            // 检查是否可能发生了位置变化（如果消息包含移动相关词汇）
            const moveKeywords = ['去', '前往', '到达', '来到', '移动', 'MOVE_TO'];
            if (moveKeywords.some(keyword => message.includes(keyword) || data.reply.includes(keyword))) {
                // 延迟刷新位置信息
                setTimeout(() => {
                    loadUserLocation();
                }, 1000);
            } else {
                // 在非移动操作后也检查事件（延迟执行，避免过于频繁）
                setTimeout(() => {
                    checkEvents();
                }, 2000);
            }
        } else {
            addMessageToChat('系统', `错误：${data.error}`, 'system');
        }
    } catch (error) {
        addMessageToChat('系统', '发送消息失败，请检查网络连接', 'system');
        console.error('发送消息错误:', error);
    } finally {
        hideTypingIndicator();
        messageInput.focus();
    }
}

// 加载角色聊天历史
async function loadCharacterHistory(character) {
    try {
        const response = await makeAuthenticatedRequest(`${API_BASE_URL}/get_character_history`, {
            method: 'POST',
            body: JSON.stringify({ character: character })
        });
        
        if (!response) return; // 认证失败已处理
        
        const data = await response.json();
        
        if (data.success) {
            // 只在非联机模式下清空聊天显示区域
            if (!isMultiplayerMode) {
                const chatDisplay = document.getElementById('chatDisplay');
                chatDisplay.innerHTML = '';
            }
            
            // 加载历史消息（在联机模式下，只加载到内存，不显示）
            if (!isMultiplayerMode) {
                data.messages.forEach(msg => {
                    if (msg.role === 'user') {
                        addMessageToChat(data.username, msg.content, 'user');
                    } else if (msg.role === 'assistant') {
                        addMessageToChat(character, msg.content, 'assistant');
                    }
                });
                
                // 滚动到底部
                const chatDisplay = document.getElementById('chatDisplay');
                chatDisplay.scrollTop = chatDisplay.scrollHeight;
            }
        }
    } catch (error) {
        console.error('加载聊天历史出错:', error);
    }
}

// 清除聊天历史
async function clearHistory() {
    const currentCharacter = document.getElementById('characterSelect').value;
    
    if (!confirm(`确定要清除与${currentCharacter}的聊天历史吗？`)) {
        return;
    }
    
    try {
        const response = await makeAuthenticatedRequest(`${API_BASE_URL}/clear`, {
            method: 'POST',
            body: JSON.stringify({ character: currentCharacter })
        });
        
        if (!response) return; // 认证失败已处理
        
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('chatDisplay').innerHTML = '';
            showMessage('聊天历史已清除', 'success');
        } else {
            showMessage('清除失败: ' + data.error, 'error');
        }
    } catch (error) {
        showMessage('清除请求失败', 'error');
        console.error('清除历史出错:', error);
    }
}

// 加载用户数据
async function loadUserData() {
    try {
        const response = await makeAuthenticatedRequest(`${API_BASE_URL}/get_user_data`, {
            method: 'POST'
        });
        
        if (!response) return; // 认证失败已处理
        
        const data = await response.json();
        
        if (data.success) {
            await updateUserDataDisplay(data.data);
            currentInventoryData = data.data;
        }
    } catch (error) {
        console.error('加载用户数据出错:', error);
    }
}

// 更新用户数据显示
async function updateUserDataDisplay(userData) {
    document.getElementById('userHP').textContent = userData.HP;
    document.getElementById('userMP').textContent = userData.MP;
    document.getElementById('userGold').textContent = userData.gold;
    
    // 更新新属性
    document.getElementById('userExperience').textContent = userData.experience || 0;
    document.getElementById('userLevel').textContent = userData.level || 1;
    
    // 显示总属性（基础+装备加成）
    const totalAttack = userData.attack || 10;
    const totalDefense = userData.defense || 5;
    const totalCriticalRate = userData.critical_rate || 5;
    const totalCriticalDamage = userData.critical_damage || 150;
    
    // 计算装备加成
    const equipBonus = userData.equipment_stats || {};
    const attackBonus = equipBonus.attack || 0;
    const defenseBonus = equipBonus.defense || 0;
    const critRateBonus = equipBonus.critical_rate || 0;
    const critDamageBonus = equipBonus.critical_damage || 0;
    
    // 显示属性（如果有装备加成则显示加成）
    document.getElementById('userAttack').textContent = attackBonus > 0 ? 
        `${totalAttack} (+${attackBonus})` : `${totalAttack}`;
    document.getElementById('userDefense').textContent = defenseBonus > 0 ? 
        `${totalDefense} (+${defenseBonus})` : `${totalDefense}`;
    document.getElementById('userCriticalRate').textContent = critRateBonus > 0 ? 
        `${totalCriticalRate}% (+${critRateBonus}%)` : `${totalCriticalRate}%`;
    document.getElementById('userCriticalDamage').textContent = critDamageBonus > 0 ? 
        `${totalCriticalDamage}% (+${critDamageBonus}%)` : `${totalCriticalDamage}%`;
    
    // 更新装备显示
    await updateEquipmentDisplay(userData.equipment);
}

// 更新装备显示
async function updateEquipmentDisplay(equipment) {
    console.log('更新装备显示，装备数据:', equipment);
    
    // 确保物品数据已加载
    if (!allItemsData) {
        console.log('物品数据未加载，正在获取...');
        try {
            const response = await fetch(`${API_BASE_URL}/get_items`);
            const data = await response.json();
            if (data.success) {
                allItemsData = data.items;
                console.log('物品数据加载成功:', Object.keys(allItemsData).length, '个物品');
            }
        } catch (error) {
            console.error('获取物品信息出错:', error);
            return;
        }
    }
    
    // 定义后端槽位名到前端元素ID的映射
    const slotMapping = {
        'weapon': 'eq-weapon',
        'armor': 'eq-chest',      
        'helmet': 'eq-head',      
        'boots': 'eq-feet',       
        'pants': 'eq-legs',       
        'shield': 'eq-accessory1',
        'accessory': 'eq-accessory2'
    };
    
    Object.keys(equipment).forEach(slot => {
        const elementId = slotMapping[slot] || `eq-${slot}`;
        const slotElement = document.getElementById(elementId);
        
        console.log(`处理槽位 ${slot}, 查找元素ID: ${elementId}`);
        
        if (slotElement) {
            if (equipment[slot]) {
                // 获取物品ID
                const itemId = equipment[slot].id || equipment[slot];
                // 显示物品名字而不是ID
                const itemInfo = allItemsData && allItemsData.find(item => item.item_id === itemId);
                const displayName = itemInfo ? itemInfo.item_name : itemId;
                
                console.log(`设置元素内容: ${displayName}`);
                slotElement.textContent = displayName;
                slotElement.classList.add('equipped');
                
                // 显示卸下按钮
                const unequipBtn = slotElement.parentElement.querySelector('.unequip-btn');
                if (unequipBtn) {
                    unequipBtn.style.display = 'inline-block';
                }
                
                console.log(`装备槽位 ${slot}: 物品ID ${itemId} -> 显示名称 ${displayName}`);
            } else {
                slotElement.textContent = '空';
                slotElement.classList.remove('equipped');
                
                // 隐藏卸下按钮
                const unequipBtn = slotElement.parentElement.querySelector('.unequip-btn');
                if (unequipBtn) {
                    unequipBtn.style.display = 'none';
                }
                
                console.log(`装备槽位 ${slot}: 空`);
            }
        } else {
            console.log(`找不到装备槽位元素: ${elementId} (槽位: ${slot})`);
        }
    });
}

// 装备物品
async function equipItem(itemId, slot) {
    try {
        const response = await makeAuthenticatedRequest(`${API_BASE_URL}/equip_item`, {
            method: 'POST',
            body: JSON.stringify({ item_id: itemId, slot: slot })
        });
        
        if (!response) return; // 认证失败已处理
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
            await loadUserData(); // 重新加载用户数据
            await updateInventoryDisplay(); // 立即更新背包显示
        } else {
            showMessage(data.message, 'error');
        }
    } catch (error) {
        showMessage('装备失败', 'error');
        console.error('装备物品出错:', error);
    }
}

// 卸下装备
async function unequipItem(slot) {
    try {
        const response = await makeAuthenticatedRequest(`${API_BASE_URL}/unequip_item`, {
            method: 'POST',
            body: JSON.stringify({ slot: slot })
        });
        
        if (!response) return; // 认证失败已处理
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
            await loadUserData(); // 重新加载用户数据
            await updateInventoryDisplay(); // 立即更新背包显示
        } else {
            showMessage(data.message, 'error');
        }
    } catch (error) {
        showMessage('卸下失败', 'error');
        console.error('卸下装备出错:', error);
    }
}

// 添加消息到聊天窗口
function addMessageToChat(sender, content, type) {
    const chatDisplay = document.getElementById('chatDisplay');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    const senderSpan = document.createElement('span');
    senderSpan.className = 'sender';
    senderSpan.textContent = sender + ': ';
    
    const contentSpan = document.createElement('span');
    contentSpan.className = 'content';
    contentSpan.textContent = content;
    
    messageDiv.appendChild(senderSpan);
    messageDiv.appendChild(contentSpan);
    
    chatDisplay.appendChild(messageDiv);
    chatDisplay.scrollTop = chatDisplay.scrollHeight;
}

// 显示输入状态指示器
function showTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.id = 'typing-indicator';
    indicator.className = 'message assistant';
    indicator.innerHTML = '<span class="content">正在思考中...</span>';
    
    document.getElementById('chatDisplay').appendChild(indicator);
    document.getElementById('chatDisplay').scrollTop = document.getElementById('chatDisplay').scrollHeight;
}

// 隐藏输入状态指示器
function hideTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

// 解析消息中的数值变化并更新用户状态
function parseAndUpdateStats(message) {
    // 简单的数值变化解析逻辑
    const hpChange = message.match(/HP\s*([+-]?\d+)/i);
    const mpChange = message.match(/MP\s*([+-]?\d+)/i);
    const goldChange = message.match(/金币\s*([+-]?\d+)/i);
    
    if (hpChange || mpChange || goldChange) {
        // 如果检测到数值变化，重新加载用户数据
        setTimeout(loadUserData, 1000);
    }
}

// 切换角色背景图片
function changeCharacterImage(character) {
    const imageElement = document.getElementById('characterImage');
    if (imageElement) {
        // 使用角色名作为图片文件名
        imageElement.src = `${API_BASE_URL}/image/${character}.jpg`;
        imageElement.onerror = function() {
            // 如果图片不存在，隐藏图片或显示占位符
            this.style.display = 'none';
            // 或者可以设置一个数据URL作为占位符
            // this.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2RkZCIvPjx0ZXh0IHg9IjUwIiB5PSI1MCIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE0IiBmaWxsPSIjOTk5IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+5rKh5pyJ5Zu+54mHPC90ZXh0Pjwvc3ZnPg==';
        };
    }
}

// 角色选择变化事件
function onCharacterChange() {
    const selectedCharacter = document.getElementById('characterSelect').value;
    loadCharacterHistory(selectedCharacter);
    changeCharacterImage(selectedCharacter);
}

// 回车键发送消息
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// 添加测试物品
async function addTestItem() {
    const itemId = document.getElementById('testItemId').value;
    const quantity = parseInt(document.getElementById('testQuantity').value) || 1;
    
    if (!itemId) {
        showMessage('请输入物品ID', 'error');
        return;
    }
    
    try {
        const response = await makeAuthenticatedRequest(`${API_BASE_URL}/add_item`, {
            method: 'POST',
            body: JSON.stringify({ item_id: itemId, quantity: quantity })
        });
        
        if (!response) return; // 认证失败已处理
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
            await loadUserData(); // 重新加载用户数据
            // 清空输入框
            document.getElementById('testItemId').value = '';
            document.getElementById('testQuantity').value = '1';
        } else {
            showMessage(data.error, 'error');
        }
    } catch (error) {
        showMessage('添加物品失败', 'error');
        console.error('添加物品出错:', error);
    }
}

// 打开背包界面
async function openInventory() {
    try {
        // 加载最新的用户数据
        await loadUserData();
        
        // 显示背包模态框
        document.getElementById('inventoryModal').style.display = 'block';
        
        // 更新背包显示
        await updateInventoryDisplay();
        
    } catch (error) {
        showMessage('打开背包失败', 'error');
        console.error('打开背包出错:', error);
    }
}

// 关闭背包界面
function closeInventory() {
    document.getElementById('inventoryModal').style.display = 'none';
}

// 更新背包显示
async function updateInventoryDisplay() {
    if (!currentInventoryData) return;
    
    // 更新装备显示
    await updateEquipmentSlots(currentInventoryData.equipment);
    
    // 更新背包物品显示
    updateInventoryGrid(currentInventoryData.inventory.items);
}

// 更新装备槽位显示
async function updateEquipmentSlots(equipment) {
    // 使用新的装备显示函数
    await updateEquipmentDisplay(equipment);
}

// 更新背包网格显示
async function updateInventoryGrid(items) {
    const inventoryGrid = document.getElementById('inventoryGrid');
    inventoryGrid.innerHTML = '';
    
    // 如果没有缓存物品数据，则获取
    if (!allItemsData) {
        try {
            const response = await fetch(`${API_BASE_URL}/get_items`);
            const data = await response.json();
            if (data.success) {
                allItemsData = data.items;
            }
        } catch (error) {
            console.error('获取物品信息出错:', error);
            return;
        }
    }
    
    items.forEach(item => {
        // 优先使用后端返回的物品信息，如果没有则从缓存查找
        const itemInfo = item.name ? item : (allItemsData ? allItemsData.find(i => i.item_id === item.id) : null) || {};
        
        // 确保有基本的显示信息
        const displayName = itemInfo.name || itemInfo.item_name || item.name || item.id;
        const description = itemInfo.description || '';
        const rarity = itemInfo.rarity || 'common';
        const itemType = itemInfo.type || itemInfo.main_type || '';
        
        console.log(`背包物品显示: ID=${item.id}, Name=${displayName}, Type=${itemType}`);
        
        const itemDiv = document.createElement('div');
        itemDiv.className = `inventory-item rarity-border-${rarity}`;
        itemDiv.title = `${displayName}\n${description}`;
        
        // 根据物品类型决定显示哪些按钮
        let actionButtons = '';
        if (itemType === 'potion' || itemType === '消耗类') {
            actionButtons = `<button class="btn-small btn-use" onclick="useItem('${item.id}', 1)">使用</button>`;
        } else if (itemType === 'weapon' || itemType === 'armor' || itemType === 'helmet' || itemType === 'boots' || itemType === 'pants' || itemType === '装备类') {
            actionButtons = `<button class="btn-small btn-equip" onclick="showEquipOptions('${item.id}')">装备</button>`;
        }
        
        itemDiv.innerHTML = `
            <div class="item-name">${displayName}</div>
            <div class="item-actions">
                ${actionButtons}
            </div>
            <div class="item-quantity">x${item.quantity}</div>
        `;
        inventoryGrid.appendChild(itemDiv);
    });
}

// 获取稀有度文本
function getRarityText(rarity) {
    const rarityMap = {
        'common': '普通',
        'uncommon': '罕见', 
        'rare': '稀有',
        'epic': '史诗',
        'legendary': '传说'
    };
    return rarityMap[rarity] || rarity;
}

// 使用物品
async function useItem(itemId, quantity = 1) {
    try {
        const response = await makeAuthenticatedRequest(`${API_BASE_URL}/use_item`, {
            method: 'POST',
            body: JSON.stringify({ item_id: itemId, quantity: quantity })
        });
        
        if (!response) return; // 认证失败已处理
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
            await loadUserData(); // 重新加载用户数据
            await updateInventoryDisplay(); // 更新背包显示
        } else {
            showMessage(data.error, 'error');
        }
    } catch (error) {
        showMessage('使用物品失败', 'error');
        console.error('使用物品出错:', error);
    }
}

// 显示装备选项 - 自动根据装备类型选择槽位
async function showEquipOptions(itemId) {
    // 获取物品信息
    if (!allItemsData) {
        try {
            const response = await fetch(`${API_BASE_URL}/get_items`);
            const data = await response.json();
            if (data.success) {
                allItemsData = data.items;
            }
        } catch (error) {
            console.error('获取物品信息出错:', error);
            showMessage('获取物品信息失败', 'error');
            return;
        }
    }
    
    // 从物品列表中查找对应的物品
    const itemInfo = allItemsData.find(item => item.item_id === itemId);
    if (!itemInfo) {
        showMessage('未找到物品信息', 'error');
        console.error('未找到物品:', itemId, '可用物品:', allItemsData);
        return;
    }
    
    // 根据item_type自动选择槽位
    let slot;
    switch (itemInfo.item_type) {
        case 'weapon':
            slot = 'weapon';
            break;
        case 'armor':
            slot = 'armor';
            break;
        case 'helmet':
            slot = 'helmet';
            break;
        case 'boots':
            slot = 'boots';
            break;
        case 'pants':
            slot = 'pants';
            break;
        case 'shield':
            slot = 'shield';
            break;
        case 'accessory':
            slot = 'accessory';
            break;
        default:
            // 如果没有明确的item_type，根据名称判断
            if (itemInfo.item_name.includes('剑') || itemInfo.item_name.includes('刀') || itemInfo.item_name.includes('匕首') || itemInfo.item_name.includes('弓') || itemInfo.item_name.includes('法杖')) {
                slot = 'weapon';
            } else if (itemInfo.item_name.includes('甲') || itemInfo.item_name.includes('袍')) {
                slot = 'armor';
            } else if (itemInfo.item_name.includes('盔') || itemInfo.item_name.includes('帽')) {
                slot = 'helmet';
            } else if (itemInfo.item_name.includes('靴') || itemInfo.item_name.includes('鞋')) {
                slot = 'boots';
            } else if (itemInfo.item_name.includes('裤') || itemInfo.item_name.includes('护腿')) {
                slot = 'pants';
            } else if (itemInfo.item_name.includes('盾')) {
                slot = 'shield';
            } else {
                slot = 'accessory';
            }
            break;
    }
    
    // 直接装备到对应槽位
    equipItem(itemId, slot);
}

// 打开物品测试界面
async function openItemTest() {
    document.getElementById('itemTestModal').style.display = 'block';
    await loadItemsForTest();
}

// 关闭物品测试界面
function closeItemTest() {
    document.getElementById('itemTestModal').style.display = 'none';
}

// 加载物品列表用于测试
async function loadItemsForTest() {
    try {
        const response = await fetch(`${API_BASE_URL}/get_items`);
        const data = await response.json();
        
        if (data.success) {
            const itemSelect = document.getElementById('itemSelect');
            itemSelect.innerHTML = '<option value="">选择物品...</option>';
            
            // data.items 是一个对象，需要遍历其键值对
            Object.entries(data.items).forEach(([itemId, item]) => {
                const option = document.createElement('option');
                option.value = itemId;
                option.textContent = `${item.name} (${itemId})`;
                itemSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('加载物品列表出错:', error);
    }
}

// 添加选中的测试物品
async function addTestItem() {
    const itemSelect = document.getElementById('itemSelect');
    const itemId = itemSelect.value;
    const quantity = parseInt(document.getElementById('itemQuantity').value) || 1;
    
    if (!itemId) {
        showMessage('请选择物品', 'error');
        return;
    }
    
    try {
        const response = await makeAuthenticatedRequest(`${API_BASE_URL}/add_item`, {
            method: 'POST',
            body: JSON.stringify({ item_id: itemId, quantity: quantity })
        });
        
        if (!response) return; // 认证失败已处理
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
            await loadUserData(); // 重新加载用户数据
        } else {
            showMessage(data.error, 'error');
        }
    } catch (error) {
        showMessage('添加物品失败', 'error');
        console.error('添加物品出错:', error);
    }
}

// 快速添加物品
async function addQuickItem(itemId, quantity) {
    try {
        const response = await makeAuthenticatedRequest(`${API_BASE_URL}/add_item`, {
            method: 'POST',
            body: JSON.stringify({ item_id: itemId, quantity: quantity })
        });
        
        if (!response) return; // 认证失败已处理
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
            await loadUserData(); // 重新加载用户数据
        } else {
            showMessage(data.error, 'error');
        }
    } catch (error) {
        showMessage('添加物品失败', 'error');
        console.error('添加物品出错:', error);
    }
}

// 过滤物品
async function filterItems(type) {
    try {
        const response = await fetch(`${API_BASE_URL}/search_items`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ main_type: type })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const itemSelect = document.getElementById('itemSelect');
            itemSelect.innerHTML = '<option value="">选择物品...</option>';
            
            // data.items 是一个对象，需要遍历其键值对
            Object.entries(data.items).forEach(([itemId, item]) => {
                const option = document.createElement('option');
                option.value = itemId;
                option.textContent = `${item.name} (${itemId})`;
                itemSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('过滤物品出错:', error);
    }
}

// 重置用户数据
async function resetUserData() {
    if (!confirm('确定要重置所有用户数据吗？这将清除你的背包和属性！')) {
        return;
    }
    
    try {
        const response = await makeAuthenticatedRequest(`${API_BASE_URL}/update_user_stats`, {
            method: 'POST',
            body: JSON.stringify({ 
                HP: 100, 
                MP: 50, 
                gold: 100,
                experience: 0,
                level: 1,
                attack: 10,
                defense: 5
            })
        });
        
        if (!response) return; // 认证失败已处理
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('用户数据已重置', 'success');
            await loadUserData(); // 重新加载用户数据
        } else {
            showMessage('重置失败: ' + data.error, 'error');
        }
    } catch (error) {
        showMessage('重置请求失败', 'error');
        console.error('重置用户数据出错:', error);
    }
}

// 保存用户数据（实际上数据是自动保存的）
function saveUserData() {
    showMessage('数据已自动保存', 'info');
}

// 编辑用户属性
async function editUserStats() {
    const currentData = await getCurrentUserData();
    
    const newHP = prompt('输入新的生命值:', currentData.HP);
    const newMP = prompt('输入新的魔法值:', currentData.MP);
    const newGold = prompt('输入新的金币数量:', currentData.gold);
    const newExperience = prompt('输入新的经验值:', currentData.experience || 0);
    const newLevel = prompt('输入新的等级:', currentData.level || 1);
    const newAttack = prompt('输入新的攻击力:', currentData.attack || 10);
    const newDefense = prompt('输入新的防御力:', currentData.defense || 5);
    const newCriticalRate = prompt('输入新的暴击率(%):', currentData.critical_rate || 5);
    const newCriticalDamage = prompt('输入新的暴击伤害(%):', currentData.critical_damage || 150);
    
    if (newHP !== null || newMP !== null || newGold !== null || 
        newExperience !== null || newLevel !== null || newAttack !== null || 
        newDefense !== null || newCriticalRate !== null || newCriticalDamage !== null) {
        
        const updateData = {};
        
        if (newHP !== null && !isNaN(newHP)) updateData.HP = parseInt(newHP);
        if (newMP !== null && !isNaN(newMP)) updateData.MP = parseInt(newMP);
        if (newGold !== null && !isNaN(newGold)) updateData.gold = parseInt(newGold);
        if (newExperience !== null && !isNaN(newExperience)) updateData.experience = parseInt(newExperience);
        if (newLevel !== null && !isNaN(newLevel)) updateData.level = parseInt(newLevel);
        if (newAttack !== null && !isNaN(newAttack)) updateData.attack = parseInt(newAttack);
        if (newDefense !== null && !isNaN(newDefense)) updateData.defense = parseInt(newDefense);
        if (newCriticalRate !== null && !isNaN(newCriticalRate)) updateData.critical_rate = parseInt(newCriticalRate);
        if (newCriticalDamage !== null && !isNaN(newCriticalDamage)) updateData.critical_damage = parseInt(newCriticalDamage);
        
        try {
            const response = await makeAuthenticatedRequest(`${API_BASE_URL}/update_user_stats`, {
                method: 'POST',
                body: JSON.stringify(updateData)
            });
            
            if (!response) return; // 认证失败已处理
            
            const data = await response.json();
            
            if (data.success) {
                showMessage('属性更新成功', 'success');
                await loadUserData(); // 重新加载用户数据
            } else {
                showMessage('更新失败: ' + data.error, 'error');
            }
        } catch (error) {
            showMessage('更新请求失败', 'error');
            console.error('更新用户属性出错:', error);
        }
    }
}

// 获取当前用户数据
async function getCurrentUserData() {
    try {
        const response = await makeAuthenticatedRequest(`${API_BASE_URL}/get_user_data`, {
            method: 'POST'
        });
        
        if (!response) return {}; // 认证失败已处理
        
        const data = await response.json();
        return data.success ? data.data : {};
    } catch (error) {
        console.error('获取用户数据出错:', error);
        return {};
    }
}

// ===== 联机功能 =====
let currentRoomId = null;
let currentRoomUsers = null;
let lastMessageTimestamp = 0;
let messagePollingInterval = null;
let isMultiplayerMode = false;

// 打开联机模态框
function openMultiplayer() {
    // 如果已经在联机模式，直接返回
    if (isMultiplayerMode) {
        showMessage('您已在联机模式中', 'info');
        return;
    }
    
    document.getElementById('multiplayerModal').style.display = 'block';
    refreshRoomList();
}

// 关闭联机模态框
function closeMultiplayer() {
    document.getElementById('multiplayerModal').style.display = 'none';
}

// 创建房间并开始游戏
async function createAndStartRoom() {
    try {
        const response = await makeAuthenticatedRequest(`${API_BASE_URL}/create_room`, {
            method: 'POST',
            body: JSON.stringify({})
        });
        
        if (!response) return;
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(`房间创建成功！房间ID: ${data.room_id}`, 'success');
            currentRoomId = data.room_id;
            await enterMultiplayerMode();
            closeMultiplayer();
        } else {
            showMessage('创建房间失败: ' + data.error, 'error');
        }
    } catch (error) {
        showMessage('创建房间请求失败', 'error');
        console.error('创建房间出错:', error);
    }
}

// 加入房间并开始游戏
async function joinAndStartRoom(roomId = null) {
    const targetRoomId = roomId || document.getElementById('roomIdInput').value.trim();
    
    if (!targetRoomId) {
        showMessage('请输入房间ID', 'error');
        return;
    }
    
    try {
        const response = await makeAuthenticatedRequest(`${API_BASE_URL}/join_room`, {
            method: 'POST',
            body: JSON.stringify({ room_id: targetRoomId })
        });
        
        if (!response) return;
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
            currentRoomId = targetRoomId;
            await enterMultiplayerMode();
            closeMultiplayer();
        } else {
            showMessage('加入房间失败: ' + data.error, 'error');
        }
    } catch (error) {
        showMessage('加入房间请求失败', 'error');
        console.error('加入房间出错:', error);
    }
}

// 进入联机模式
async function enterMultiplayerMode() {
    isMultiplayerMode = true;
    
    // 显示联机状态
    document.getElementById('multiplayerStatus').style.display = 'block';
    document.getElementById('roomIdDisplay').textContent = currentRoomId;
    
    // 显示互动控制
    document.getElementById('multiplayerInteraction').style.display = 'block';
    
    // 更新联机按钮文本
    const multiplayerBtn = document.querySelector('.btn-multiplayer');
    multiplayerBtn.textContent = '🌐 联机中';
    multiplayerBtn.style.background = '#67c23a';
    
    // 加载龙与地下城角色历史（主持人提示词）
    console.log('正在加载主持人提示词...');
    
    // 设置角色选择器为龙与地下城
    const characterSelect = document.getElementById('characterSelect');
    characterSelect.value = '龙与地下城';
    
    await loadCharacterHistory('龙与地下城');
    changeCharacterImage('龙与地下城');
    console.log('主持人提示词加载完成');
    
    // 开始轮询房间信息
    startMultiplayerPolling();
    
    showMessage('已进入联机模式，可以正常游戏并与其他玩家互动！', 'success');
}

// 离开联机房间
async function leaveMultiplayerRoom() {
    if (!currentRoomId) return;
    
    try {
        const response = await makeAuthenticatedRequest(`${API_BASE_URL}/leave_room`, {
            method: 'POST',
            body: JSON.stringify({ room_id: currentRoomId })
        });
        
        if (response) {
            const data = await response.json();
            if (data.success) {
                showMessage(data.message, 'success');
            }
        }
    } catch (error) {
        console.error('离开房间出错:', error);
    }
    
    // 退出联机模式
    exitMultiplayerMode();
}

// 退出联机模式
function exitMultiplayerMode() {
    isMultiplayerMode = false;
    currentRoomId = null;
    currentRoomUsers = null;
    lastMessageTimestamp = 0;
    
    // 停止消息轮询
    if (messagePollingInterval) {
        clearInterval(messagePollingInterval);
        messagePollingInterval = null;
    }
    
    // 隐藏联机状态和控制
    document.getElementById('multiplayerStatus').style.display = 'none';
    document.getElementById('multiplayerInteraction').style.display = 'none';
    
    // 恢复联机按钮
    const multiplayerBtn = document.querySelector('.btn-multiplayer');
    multiplayerBtn.textContent = '🌐 联机游戏';
    multiplayerBtn.style.background = '#67c23a';
    
    showMessage('已退出联机模式', 'info');
}

// 开始联机轮询
function startMultiplayerPolling() {
    loadRoomInfo();
    startMessagePolling();
}

// 加载房间信息
async function loadRoomInfo() {
    if (!currentRoomId) return;
    
    try {
        const response = await makeAuthenticatedRequest(`${API_BASE_URL}/get_room_info`, {
            method: 'POST',
            body: JSON.stringify({ room_id: currentRoomId })
        });
        
        if (!response) return;
        
        const data = await response.json();
        
        if (data.success) {
            const roomInfo = data.room_info;
            const currentUsername = localStorage.getItem('currentUser');
            
            // 更新互动对象选择
            updateInteractionTargets(roomInfo.users, currentUsername);
        }
    } catch (error) {
        console.error('获取房间信息出错:', error);
    }
}

// 联机模式下不需要单独的用户列表显示

// 更新互动对象选择
function updateInteractionTargets(users, currentUsername) {
    const targetSelect = document.getElementById('interactionTarget');
    const currentValue = targetSelect.value; // 保存当前选择
    
    targetSelect.innerHTML = '<option value="">选择互动对象...</option>';
    
    users.forEach(user => {
        if (user.username !== currentUsername) {
            const option = document.createElement('option');
            option.value = user.username;
            option.textContent = user.username;
            targetSelect.appendChild(option);
        }
    });
    
    // 恢复之前的选择（如果该用户仍在房间内）
    if (currentValue && users.some(user => user.username === currentValue)) {
        targetSelect.value = currentValue;
    }
}

// 发送消息到房间（内部函数）
async function sendToRoom(sender, content, messageType, targetUser = null) {
    if (!currentRoomId) return;
    
    try {
        await makeAuthenticatedRequest(`${API_BASE_URL}/send_room_message`, {
            method: 'POST',
            body: JSON.stringify({
                room_id: currentRoomId,
                content: content,
                message_type: messageType,
                target_user: targetUser,
                sender_override: sender  // 允许设置发送者名称
            })
        });
    } catch (error) {
        console.error('发送房间消息出错:', error);
    }
}



// 创建选项按钮
function createOptionButtons(content, messageId) {
    // 查找选项模式，按行处理
    const targetMatch = content.match(/@(\w+)/);
    
    if (!targetMatch) return null;
    
    const targetPlayer = targetMatch[1];
    const currentUser = currentRoomId ? localStorage.getItem('currentUser') : gameState.currentUser;
    
    // 只为目标玩家显示按钮（忽略大小写）
    if (currentUser.toLowerCase() !== targetPlayer.toLowerCase()) {
        return null;
    }
    
    // 按行拆分，查找A) B) C)选项
    const lines = content.split('\n');
    const options = [];
    
    lines.forEach(line => {
        const trimmedLine = line.trim();
        const optionMatch = trimmedLine.match(/^([ABC])\)\s*(.+)$/);
        if (optionMatch) {
            options.push({
                key: optionMatch[1],
                text: optionMatch[2].trim()
            });
        }
    });
    
    if (options.length === 0) return null;
    
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'choice-buttons';
    buttonContainer.style.cssText = `
        margin-top: 10px;
        display: flex;
        flex-direction: column;
        gap: 8px;
        padding: 8px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    `;
    
    options.forEach(option => {
        const button = document.createElement('button');
        button.textContent = `${option.key}) ${option.text}`;
        button.className = 'choice-button';
        button.style.cssText = `
            padding: 10px 16px;
            background: linear-gradient(135deg, #4a90e2, #357abd);
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s ease;
            text-align: left;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        `;
        
        button.addEventListener('mouseover', () => {
            button.style.background = 'linear-gradient(135deg, #357abd, #2a5f99)';
            button.style.transform = 'translateY(-1px)';
            button.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
        });
        
        button.addEventListener('mouseout', () => {
            button.style.background = 'linear-gradient(135deg, #4a90e2, #357abd)';
            button.style.transform = 'translateY(0)';
            button.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
        });
        
        button.addEventListener('click', () => {
            selectChoice(option.key, option.text, buttonContainer);
        });
        
        buttonContainer.appendChild(button);
    });
    
    return buttonContainer;
}

// 触发AI主持人回应
async function triggerAIResponse(playerChoice) {
    if (!currentRoomId) return;
    
    try {
        console.log('触发AI回应，玩家选择:', playerChoice);
        const currentPlayer = localStorage.getItem('currentUser');
        const response = await makeAuthenticatedRequest(`${API_BASE_URL}/trigger_dm_response`, {
            method: 'POST',
            body: JSON.stringify({
                room_id: currentRoomId,
                interaction_content: `${currentPlayer}做出了选择：${playerChoice}。请作为D&D主持人描述这个行动的结果和后续发展，直接使用玩家名"${currentPlayer}"而不是占位符。`,
                original_sender: currentPlayer,
                target_user: 'all'
            })
        });
        
        if (response && response.ok) {
            console.log('AI回应触发成功');
            // 延迟刷新以等待AI响应
            setTimeout(() => {
                loadRoomMessages();
            }, 2000);
        }
    } catch (error) {
        console.error('触发AI回应失败:', error);
    }
}

// 选择选项
async function selectChoice(choiceKey, choiceText, buttonContainer) {
    // 发送选择到聊天
    const message = `我选择 ${choiceKey}：${choiceText}`;
    
    if (currentRoomId) {
        try {
            const response = await makeAuthenticatedRequest(`${API_BASE_URL}/send_room_message`, {
                method: 'POST',
                body: JSON.stringify({
                    room_id: currentRoomId,
                    message: message
                })
            });
            
            if (response && response.ok) {
                console.log('选择已发送:', message);
                // 立即刷新消息以显示选择结果
                setTimeout(() => {
                    loadRoomMessages();
                }, 500);
                
                // 触发AI主持人对选择的回应
                setTimeout(() => {
                    triggerAIResponse(message);
                }, 1000);
            }
        } catch (error) {
            console.error('发送选择失败:', error);
            showMessage('发送选择失败', 'error');
            return;
        }
    }
    
    // 禁用所有按钮
    const buttons = buttonContainer.querySelectorAll('.choice-button');
    buttons.forEach(btn => {
        btn.disabled = true;
        btn.style.opacity = '0.6';
        btn.style.cursor = 'not-allowed';
    });
    
    // 高亮选中的按钮
    const selectedButton = Array.from(buttons).find(btn => 
        btn.textContent.startsWith(`${choiceKey})`));
    if (selectedButton) {
        selectedButton.style.background = 'linear-gradient(135deg, #28a745, #1e7e34)';
        selectedButton.style.opacity = '1';
        selectedButton.style.transform = 'scale(0.98)';
    }
}

// 发送互动消息
async function sendInteraction() {
    const target = document.getElementById('interactionTarget').value;
    const message = document.getElementById('interactionMessage').value.trim();
    
    console.log('=== 发送互动消息 ===');
    console.log('目标用户:', target);
    console.log('消息内容:', message);
    console.log('当前房间ID:', currentRoomId);
    
    if (!target) {
        console.error('错误: 未选择互动对象');
        showMessage('请选择互动对象', 'error');
        return;
    }
    
    if (!message) {
        console.error('错误: 消息内容为空');
        showMessage('请输入互动内容', 'error');
        return;
    }
    
    try {
        const requestBody = {
            room_id: currentRoomId,
            content: message,
            message_type: 'interaction',
            target_user: target
        };
        console.log('发送请求数据:', requestBody);
        
        const response = await makeAuthenticatedRequest(`${API_BASE_URL}/send_room_message`, {
            method: 'POST',
            body: JSON.stringify(requestBody)
        });
        
        console.log('服务器响应:', response);
        
        if (!response) {
            console.error('错误: 服务器无响应');
            return;
        }
        
        const data = await response.json();
        console.log('响应数据:', data);
        
        if (data.success) {
            document.getElementById('interactionMessage').value = '';
            console.log('✅ 互动消息发送成功');
            showMessage('互动消息发送成功', 'success');
            
            // 立即刷新消息显示
            console.log('刷新消息显示...');
            await loadRoomMessages();
            
            // 主动触发主持人回应
            console.log('触发主持人回应...');
            try {
                const currentUsername = localStorage.getItem('currentUser');
                const dmResponse = await makeAuthenticatedRequest(`${API_BASE_URL}/trigger_dm_response`, {
                    method: 'POST',
                    body: JSON.stringify({
                        room_id: currentRoomId,
                        interaction_content: `${currentUsername}对${target}说：${message}`,
                        original_sender: currentUsername,
                        target_user: target
                    })
                });
                
                if (dmResponse) {
                    const dmData = await dmResponse.json();
                    console.log('主持人回应触发结果:', dmData);
                }
            } catch (error) {
                console.error('触发主持人回应失败:', error);
            }
            
            // 等待2秒后刷新消息，获取主持人回应
            setTimeout(async () => {
                console.log('获取主持人回应...');
                await loadRoomMessages();
            }, 2000);
        } else {
            console.error('❌ 发送失败:', data.error);
            showMessage('发送失败: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('❌ 发送互动消息出错:', error);
        console.error('错误详情:', error.stack);
        showMessage('发送互动消息失败: ' + error.message, 'error');
    }
}

// 开始消息轮询
function startMessagePolling() {
    if (messagePollingInterval) {
        clearInterval(messagePollingInterval);
    }
    
    messagePollingInterval = setInterval(loadRoomMessages, 5000);
    loadRoomMessages(); // 立即加载一次
}

// 加载房间消息
async function loadRoomMessages() {
    if (!currentRoomId) return;
    
    console.log('=== 加载房间消息 ===');
    console.log('房间ID:', currentRoomId);
    console.log('上次消息时间戳:', lastMessageTimestamp);
    
    try {
        const requestBody = {
            room_id: currentRoomId,
            since_timestamp: lastMessageTimestamp
        };
        
        console.log('请求参数:', requestBody);
        
        const response = await makeAuthenticatedRequest(`${API_BASE_URL}/get_room_messages`, {
            method: 'POST',
            body: JSON.stringify(requestBody)
        });
        
        if (!response) {
            console.error('错误: 获取消息时服务器无响应');
            return;
        }
        
        const data = await response.json();
        console.log('获取到的消息数据:', data);
        
        if (data.success) {
            console.log('收到消息数量:', data.messages ? data.messages.length : 0);
            // 将房间消息显示在主聊天窗口
            displayRoomMessagesInChat(data.messages);
            
            // 更新房间信息（只在用户列表变化时更新）
            if (data.room_info) {
                const currentUsername = localStorage.getItem('currentUser');
                const newUserList = data.room_info.users.map(u => u.username).sort();
                const oldUserList = currentRoomUsers ? currentRoomUsers.map(u => u.username).sort() : [];
                
                // 只有当用户列表发生变化时才更新选择框
                if (JSON.stringify(newUserList) !== JSON.stringify(oldUserList)) {
                    updateInteractionTargets(data.room_info.users, currentUsername);
                    currentRoomUsers = data.room_info.users;
                }
            }
        }
    } catch (error) {
        console.error('获取房间消息出错:', error);
    }
}

// 在主聊天窗口显示房间消息
function displayRoomMessagesInChat(messages) {
    console.log('=== 显示房间消息 ===');
    console.log('消息列表:', messages);
    
    const chatDisplay = document.querySelector('.chat-display');
    
    messages.forEach(msg => {
        console.log('处理消息:', msg);
        if (msg.timestamp > lastMessageTimestamp) {
            console.log('显示新消息:', msg.content, '时间戳:', msg.timestamp);
            const messageElement = document.createElement('div');
            messageElement.className = 'message';
            
            const time = new Date(msg.timestamp * 1000).toLocaleTimeString();
            
            // 根据消息类型设置不同的显示样式
            let messageClass = '';
            let messagePrefix = '';
            
            if (msg.message_type === 'interaction') {
                messageClass = 'interaction-message';
                messagePrefix = '🎭 ';
            } else if (msg.message_type === 'global') {
                messageClass = 'global-message';
                messagePrefix = '📢 ';
            } else if (msg.sender === '系统') {
                messageClass = 'system-message';
                messagePrefix = '🤖 ';
            } else if (msg.sender === '龙与地下城') {
                messageClass = 'dm-message';
                messagePrefix = '🎲 ';
            }
            
            console.log(`消息类型: ${msg.message_type}, 发送者: ${msg.sender}, 样式: ${messageClass}`);
            
            messageElement.className = `message ${messageClass}`;
            
            messageElement.innerHTML = `
                <div class="message-header">
                    <span class="message-role">${messagePrefix}${msg.sender}</span>
                    <span class="message-time">${time}</span>
                </div>
                <div class="message-content">${msg.content}</div>
            `;
            
            // 检查是否是主持人消息且包含选项
            if (msg.sender === '龙与地下城' && msg.content.includes('@')) {
                const optionButtons = createOptionButtons(msg.content, msg.id);
                if (optionButtons) {
                    messageElement.appendChild(optionButtons);
                }
            }
            
            chatDisplay.appendChild(messageElement);
            lastMessageTimestamp = Math.max(lastMessageTimestamp, msg.timestamp);
        }
    });
    
    // 滚动到底部
    chatDisplay.scrollTop = chatDisplay.scrollHeight;
}

// 刷新房间列表
async function refreshRoomList() {
    try {
        const response = await fetch(`${API_BASE_URL}/get_room_list`);
        const data = await response.json();
        
        if (data.success) {
            displayRoomList(data.rooms);
        }
    } catch (error) {
        console.error('获取房间列表出错:', error);
    }
}

// 显示房间列表
function displayRoomList(rooms) {
    const roomsList = document.getElementById('roomsList');
    roomsList.innerHTML = '';
    
    if (rooms.length === 0) {
        roomsList.innerHTML = '<p style="text-align: center; color: #909399;">暂无可用房间</p>';
        return;
    }
    
    rooms.forEach(room => {
        const roomItem = document.createElement('div');
        roomItem.className = 'room-item';
        
        const isFull = room.user_count >= room.max_users;
        
        roomItem.innerHTML = `
            <div class="room-info">
                <div class="room-id">房间: ${room.room_id}</div>
                <div class="room-details">
                    房主: ${room.host} | 
                    人数: ${room.user_count}/${room.max_users}
                </div>
            </div>
            <button class="room-join-btn" onclick="joinAndStartRoom('${room.room_id}')" ${isFull ? 'disabled' : ''}>
                ${isFull ? '已满' : '加入'}
            </button>
        `;
        
        roomsList.appendChild(roomItem);
    });
}

// ======= 地图系统功能 =======

// 加载用户位置信息
async function loadUserLocation() {
    try {
        const response = await makeAuthenticatedRequest(`${API_BASE_URL}/get_user_location`);
        
        if (!response) return;
        
        const data = await response.json();
        
        if (data.success && data.location) {
            updateLocationDisplay(data.location);
            await loadAreaLocations(data.location.current_area);
        }
    } catch (error) {
        console.error('加载用户位置失败:', error);
    }
}

// 更新位置显示
function updateLocationDisplay(location) {
    document.getElementById('currentLocation').textContent = location.location_display_name || '未知位置';
    document.getElementById('locationDescription').textContent = location.location_description || '暂无描述';
}

// 加载区域内的地点 (已简化，不再自动显示地点列表)
async function loadAreaLocations(areaName = 'novice_village') {
    // 不再自动显示地点列表，现在通过地图按钮查看
    // 这个函数保留是为了兼容性，但不执行任何操作
    console.log('地点列表现在通过地图按钮查看');
}

// 显示地点信息
function displayLocationButtons(locations) {
    const locationList = document.getElementById('locationList');
    locationList.innerHTML = '';
    
    // 获取当前位置
    const currentLocation = document.getElementById('currentLocation').textContent;
    
    // 按区域分组
    const locationsByArea = {};
    locations.forEach(location => {
        if (!location.is_accessible) return; // 跳过不可访问的地点
        
        const areaName = location.area_display_name || '未知区域';
        if (!locationsByArea[areaName]) {
            locationsByArea[areaName] = [];
        }
        locationsByArea[areaName].push(location);
    });
    
    // 显示各区域的地点
    Object.keys(locationsByArea).forEach(areaName => {
        // 创建区域标题
        const areaTitle = document.createElement('div');
        areaTitle.className = 'area-title';
        areaTitle.textContent = areaName;
        locationList.appendChild(areaTitle);
        
        // 显示该区域的地点
        locationsByArea[areaName].forEach(location => {
            const item = document.createElement('div');
            item.className = `location-item ${location.location_type}`;
            
            // 如果是当前位置，添加特殊样式
            if (location.display_name === currentLocation) {
                item.classList.add('current');
            }
            
            // 移动功能已禁用 - 需要通过与主持人对话来移动
            // item.addEventListener('click', () => {
            //     moveToLocation(location.location_name);
            // });
            
            item.innerHTML = `
                <div class="location-icon"></div><span class="location-name">${location.display_name}</span>
                <div class="location-desc">${location.description || ''}</div>
            `;
            
            item.title = `${location.display_name}: ${location.description} (需要与主持人说话才能移动)`;
            
            locationList.appendChild(item);
        });
    });
}

// 移动到指定地点 (已禁用 - 需要通过主持人对话移动)
async function moveToLocation(locationName) {
    // 移动功能已禁用 - 玩家需要通过与主持人对话来移动
    showMessage('🚫 直接移动已禁用！请与主持人说话，描述你想要去的地方，例如："我想去铁匠铺"', 'warning');
    return;
    
    // 以下代码已禁用
    /*
    try {
        const response = await makeAuthenticatedRequest(`${API_BASE_URL}/move_to_location`, {
            method: 'POST',
            body: JSON.stringify({
                location: locationName
            })
        });
        
        if (!response) return;
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(`成功移动到 ${data.new_location}`, 'success');
            await loadUserLocation(); // 重新加载位置信息
        } else {
            showMessage(`移动失败: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('移动失败:', error);
        showMessage('移动失败，请重试', 'error');
    }
    */
}



// 在用户数据加载时同时加载位置信息
const originalLoadUserData = loadUserData;
loadUserData = async function() {
    await originalLoadUserData.call(this);
    await loadUserLocation();
};

// ======= 商店系统功能 =======

// 检查当前位置（直接显示位置互动，不再显示默认内容）
async function checkCurrentShop() {
    try {
        console.log('🔍 检查当前位置...');
        // 直接显示位置互动选项
        await showLocationInteractions();
    } catch (error) {
        console.error('❌ 检查位置失败:', error);
        showDefaultContent();
    }
}

// 显示商店按钮
// 已移除 showShopButton，彻底不再显示商店按钮

// 隐藏商店按钮
// 已移除 hideShopButton，彻底不再隐藏商店按钮

// 打开商店
async function openShop(shopInfo) {
    try {
        // 显示商店界面
        document.getElementById('shopSection').style.display = 'block';
        document.getElementById('shopName').textContent = shopInfo.display_name;
        document.getElementById('shopDescription').textContent = shopInfo.description;
        
        // 加载商店商品
        await loadShopItems(shopInfo.shop_name);
        
        // 滚动到商店区域
        document.getElementById('shopSection').scrollIntoView({ behavior: 'smooth' });
        
    } catch (error) {
        console.error('打开商店失败:', error);
        showMessage('无法打开商店', 'error');
    }
}

// 加载商店商品
async function loadShopItems(shopName) {
    try {
        console.log('🛒 开始加载商店商品, shopName:', shopName);
        const url = `${API_BASE_URL}/get_shop_items?shop_name=${shopName}`;
        console.log('📡 请求URL:', url);
        
        const response = await makeAuthenticatedRequest(url);
        console.log('📥 服务器响应:', response);
        
        if (!response) {
            console.log('❌ 没有收到响应');
            return;
        }
        
        const data = await response.json();
        console.log('📦 响应数据:', data);
        
        if (data.success && data.items) {
            console.log('✅ 成功获取商品列表，共', data.items.length, '件商品');
            displayShopItems(data.items, shopName);
        } else {
            console.log('❌ 服务器返回错误:', data.error || '未知错误');
            showMessage('无法加载商店商品', 'error');
        }
    } catch (error) {
        console.error('❌ 加载商店商品失败:', error);
        showMessage('加载商店商品失败', 'error');
    }
}

// 显示商店商品
function displayShopItems(items, shopName) {
    console.log('🎪 开始显示商店商品:', shopName, '商品数量:', items.length);
    const shopItemsContainer = document.getElementById('dynamicShopItems');
    console.log('📍 商品容器元素:', shopItemsContainer);
    
    shopItemsContainer.innerHTML = '';
    
    if (items.length === 0) {
        console.log('⚠️ 商品列表为空');
        shopItemsContainer.innerHTML = '<div style="text-align: center; padding: 20px; color: #909399;">暂无商品</div>';
        return;
    }
    
    console.log('📋 商品详细信息:', items);
    
    items.forEach(item => {
        const isOutOfStock = item.stock === 0;
        const stockText = item.stock === -1 ? '充足' : `剩余 ${item.stock}`;
        
        const itemElement = document.createElement('div');
        itemElement.className = `shop-item ${isOutOfStock ? 'out-of-stock' : ''}`;
        
        itemElement.innerHTML = `
            <div class="shop-item-header">
                <div class="shop-item-name">${item.name}</div>
                <div class="shop-item-price">💰${item.price}</div>
            </div>
            <div class="shop-item-description">${item.description}</div>
            <div class="shop-item-footer">
                <div class="shop-item-stock">库存: ${stockText}</div>
                <button class="shop-item-buy" 
                        onclick="purchaseItem('${shopName}', '${item.id}', ${item.price}, '${item.name}')"
                        ${isOutOfStock ? 'disabled' : ''}>
                    ${isOutOfStock ? '缺货' : '购买'}
                </button>
            </div>
        `;
        
        shopItemsContainer.appendChild(itemElement);
    });
}

// 购买商品
async function purchaseItem(shopName, itemId, price, itemName) {
    try {
        const userGold = parseInt(document.getElementById('userGold').textContent) || 0;
        
        if (userGold < price) {
            showMessage('金币不足！', 'error');
            return;
        }
        
        if (!confirm(`确定要花费 ${price} 金币购买 ${itemName} 吗？`)) {
            return;
        }
        
        const response = await makeAuthenticatedRequest(`${API_BASE_URL}/purchase_item`, {
            method: 'POST',
            body: JSON.stringify({
                shop_name: shopName,
                item_id: itemId,
                price: price
            })
        });
        
        if (!response) return;
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(`成功购买 ${itemName}！`, 'success');
            // 刷新用户数据和商店商品
            await loadUserData();
            await loadShopItems(shopName);
            // 同时刷新动态内容区域的商品显示
            await loadDynamicShopItems(shopName);
        } else {
            showMessage(data.error || '购买失败', 'error');
        }
    } catch (error) {
        console.error('购买失败:', error);
        showMessage('购买失败', 'error');
    }
}

// 关闭商店
function closeShop() {
    document.getElementById('shopSection').style.display = 'none';
}

// ======= 动态内容区域管理 =======

// 显示默认内容（角色信息）
function showDefaultContent() {
    console.log('显示默认内容');
    // 先移除之前的样式，再设置新的
    const defaultEl = document.getElementById('defaultContent');
    defaultEl.style.removeProperty('display');
    defaultEl.style.display = 'flex';
    
    // 隐藏其他区域
    document.getElementById('shopContentArea').style.display = 'none';
    document.getElementById('battleContentArea').style.display = 'none';
    document.getElementById('locationInteractionArea').style.display = 'none';
}

// 显示商店内容
function showShopContent() {
    // 先移除之前的样式，再设置新的
    const shopEl = document.getElementById('shopContentArea');
    shopEl.style.removeProperty('display');
    shopEl.style.display = 'flex';
    
    // 隐藏其他区域
    document.getElementById('defaultContent').style.display = 'none';
    document.getElementById('battleContentArea').style.display = 'none';
    document.getElementById('locationInteractionArea').style.display = 'none';
}

// 显示战斗内容
function showBattleContent() {
    // 先移除之前的样式，再设置新的
    const battleEl = document.getElementById('battleContentArea');
    battleEl.style.removeProperty('display');
    battleEl.style.display = 'flex';
    
    // 隐藏其他区域
    document.getElementById('defaultContent').style.display = 'none';
    document.getElementById('shopContentArea').style.display = 'none';
    document.getElementById('locationInteractionArea').style.display = 'none';
}

// 加载并显示商店内容
async function loadAndShowShopContent(shopInfo) {
    try {
        console.log('🏗️ 开始加载商店内容:', shopInfo);
        
        // 检查HTML元素是否存在
        const shopNameEl = document.getElementById('dynamicShopName');
        const shopDescEl = document.getElementById('dynamicShopDesc');
        
        if (!shopNameEl || !shopDescEl) {
            console.error('❌ 商店HTML元素不存在! dynamicShopName:', !!shopNameEl, 'dynamicShopDesc:', !!shopDescEl);
            showDefaultContent();
            return;
        }
        
        // 更新商店标题
        shopNameEl.textContent = shopInfo.display_name;
        shopDescEl.textContent = shopInfo.description;
        console.log('✅ 更新商店标题:', shopInfo.display_name);
        
        // 加载商店商品
        console.log('📦 开始加载商店商品，商店名称:', shopInfo.shop_name);
        await loadDynamicShopItems(shopInfo.shop_name);
        
        // 显示商店内容
        console.log('🎯 显示商店内容');
        showShopContent();
        
    } catch (error) {
        console.error('❌ 加载商店内容失败:', error);
        showDefaultContent();
    }
}

// 加载动态商店商品
async function loadDynamicShopItems(shopName) {
    try {
        console.log('🛒 请求商店商品，URL:', `${API_BASE_URL}/get_shop_items?shop_name=${shopName}`);
        const response = await makeAuthenticatedRequest(`${API_BASE_URL}/get_shop_items?shop_name=${shopName}`);
        
        if (!response) {
            console.log('❌ 商品请求无响应');
            return;
        }
        
        const data = await response.json();
        console.log('📦 商品数据响应:', data);
        
        if (data.success && data.items) {
            console.log('✅ 成功获取', data.items.length, '个商品');
            displayDynamicShopItems(data.items, shopName);
        } else {
            console.log('⚠️ 商品数据获取失败或为空:', data);
        }
    } catch (error) {
        console.error('❌ 加载动态商店商品失败:', error);
    }
}

// 显示动态商店商品
function displayDynamicShopItems(items, shopName) {
    console.log('🎨 开始显示商品，商品数量:', items.length);
    
    const shopItemsContainer = document.getElementById('dynamicShopItems');
    if (!shopItemsContainer) {
        console.error('❌ 商品容器元素不存在! dynamicShopItems');
        return;
    }
    
    console.log('✅ 找到商品容器元素');
    shopItemsContainer.innerHTML = '';
    
    if (items.length === 0) {
        console.log('📭 商品列表为空，显示提示信息');
        shopItemsContainer.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #909399;">暂无商品</div>';
        return;
    }
    
    items.forEach(item => {
        console.log('🎨 渲染商品:', item);
        
        const isOutOfStock = item.stock === 0;
        const stockText = item.stock === -1 ? '充足' : `库存 ${item.stock}`;
        
        // 使用和背包相同的显示风格
        const itemElement = document.createElement('div');
        itemElement.className = `inventory-item rarity-border-${item.rarity} ${isOutOfStock ? 'out-of-stock' : ''}`;
        itemElement.title = `${item.name}\n${item.description}\n价格: ${item.price}金币\n${stockText}`;
        
        itemElement.innerHTML = `
            <div class="item-name">${item.name}</div>
            <div class="item-actions">
                <button class="btn-small btn-buy" 
                        onclick="purchaseItem('${shopName}', '${item.id}', ${item.price}, '${item.name}')"
                        ${isOutOfStock ? 'disabled' : ''}>
                    ${isOutOfStock ? '缺货' : `💰${item.price}`}
                </button>
            </div>
            <div class="item-quantity">${stockText}</div>
        `;
        
        shopItemsContainer.appendChild(itemElement);
    });
}

// 根据物品类型获取图标
function getItemIcon(itemType) {
    const icons = {
        'weapon': '⚔️',
        'armor': '🛡️',
        'potion': '🧪',
        'consumable': '🍄',
        'accessory': '💍',
        'tool': '🔧',
        'default': '📦'
    };
    return icons[itemType] || icons['default'];
}

// 根据物品子类型获取详细图标
function getItemIconBySubType(subType) {
    const icons = {
        // 武器类
        'weapon': '⚔️',
        
        // 防具类
        'head': '⛑️',      // 头盔
        'chest': '🦺',     // 胸甲
        'legs': '👖',      // 护腿
        'feet': '👢',      // 靴子
        
        // 饰品类
        'accessory': '💍',
        
        // 消耗品类
        'potion': '🧪',
        
        // 任务物品
        'quest': '📜',
        
        // 默认
        'default': '📦'
    };
    
    return icons[subType] || icons['default'];
}

// 修改位置加载函数，同时检查商店和事件
const originalLoadUserLocation = loadUserLocation;
loadUserLocation = async function() {
    await originalLoadUserLocation.call(this);
    await checkCurrentShop();
    await checkLocationEvents();
};

// ======= 事件系统 =======

// 检查位置相关事件（如村外森林哥布林战斗）
async function checkLocationEvents() {
    try {
        // 先检查常规事件
        await checkEvents();
        

    } catch (error) {
        console.error('检查位置事件失败:', error);
    }
}

// ======= 位置互动系统 =======

// 检查并显示当前位置对应的内容
async function checkAndShowLocationContent() {
    console.log('🔍 检查当前位置并显示对应内容...');
    
    try {
        // 获取当前位置
        const currentLocation = await getCurrentLocation();
        if (!currentLocation) {
            console.log('无法获取当前位置信息，显示默认内容');
            showDefaultContent();
            return;
        }
        
        console.log('当前位置:', currentLocation);
        
        // 检查当前位置是否有特殊互动
        const hasInteractions = await checkLocationHasInteractions(currentLocation);
        
        if (hasInteractions) {
            console.log('当前位置有互动选项，显示位置互动界面');
            await showLocationInteractions();
        } else {
            console.log('当前位置无特殊互动，显示默认内容');
            showDefaultContent();
        }
    } catch (error) {
        console.error('检查位置内容失败:', error);
        // 出错时显示默认内容
        showDefaultContent();
    }
}

// 显示位置互动选项
async function showLocationInteractions() {
    try {
        // 获取当前位置
        const currentLocation = await getCurrentLocation();
        if (!currentLocation) {
            console.log('无法获取当前位置信息，显示默认内容');
            showDefaultContent();
            return;
        }
        
        // 检查当前位置是否有特殊互动
        const hasInteractions = await checkLocationHasInteractions(currentLocation);
        
        if (hasInteractions) {
            console.log('有互动选项，开始显示位置互动界面');
            // 隐藏其他内容区域
            hideAllContentAreas();
            console.log('已隐藏所有内容区域');
            
            // 显示位置互动区域
            const interactionArea = document.getElementById('locationInteractionArea');
            console.log('位置互动区域元素:', interactionArea);
            // 先移除之前的样式，再设置新的
            interactionArea.style.removeProperty('display');
            interactionArea.style.display = 'flex';
            console.log('已设置位置互动区域为显示，新样式:', interactionArea.style.display);
            
            // 根据当前位置显示不同的互动选项
            await updateInteractionOptions(currentLocation);
            console.log('已更新互动选项');
        } else {
            console.log('没有互动选项，显示默认内容');
            // 没有特殊互动，显示默认内容
            showDefaultContent();
        }
        
    } catch (error) {
        console.error('显示位置互动失败:', error);
        showDefaultContent();
    }
}

// 检查位置是否有特殊互动选项
async function checkLocationHasInteractions(locationData) {
    console.log('检查位置互动，当前位置数据:', locationData);
    const currentLocationName = locationData.current_location;
    console.log('当前位置名称:', currentLocationName);
    
    // 获取位置配置数据来判断是否有互动
    try {
        const response = await makeAuthenticatedRequest(`${API_BASE_URL}/get_location_info?location=${currentLocationName}`);
        if (response && response.ok) {
            const data = await response.json();
            if (data.success && data.location) {
                const interactions = data.location.interactions || [];
                const hasInteractions = interactions.length > 0;
                console.log('位置互动选项:', interactions, '是否有互动:', hasInteractions);
                return hasInteractions;
            }
        }
    } catch (error) {
        console.error('获取位置信息失败:', error);
    }
    
    // 如果无法获取位置信息，返回 false
    console.log('无法获取位置信息，假设无互动');
    return false;
}

// 更新互动选项
async function updateInteractionOptions(locationData) {
    console.log('更新互动选项，位置数据:', locationData);
    const optionsContainer = document.getElementById('interactionOptions');
    console.log('互动选项容器:', optionsContainer);
    
    // 清空现有选项
    optionsContainer.innerHTML = '';
    console.log('已清空现有选项');
    
    const currentLocationName = locationData.current_location;
    console.log('开始为位置添加选项:', currentLocationName);
    
    // 获取位置配置数据来动态生成互动选项
    try {
        const response = await makeAuthenticatedRequest(`${API_BASE_URL}/get_location_info?location=${currentLocationName}`);
        if (response && response.ok) {
            const data = await response.json();
            if (data.success && data.location) {
                const interactions = data.location.interactions || [];
                
                console.log('位置互动配置:', interactions);
                
                console.log('位置特性:', features, '位置类型:', locationType);
                
                // 根据位置特性动态添加互动选项
                features.forEach(feature => {
                    switch (feature) {
                        case 'rest':
                            addInteractionOption(optionsContainer, {
                                icon: '💤',
                                title: '休息恢复',
                                description: '恢复生命值和法力值',
                                action: () => restAtHome()
                            });
                            break;
                            
                        case 'storage':
                            addInteractionOption(optionsContainer, {
                                icon: '⚔️',
                                title: '与木偶假人战斗',
                                description: '安全的战斗训练，不会受到真正的伤害',
                                action: () => startTrainingDummyBattle()
                            });
                            break;
                            
                        case 'equipment_shop':
                            addInteractionOption(optionsContainer, {
                                icon: '🛒',
                                title: '购买装备',
                                description: '查看武器和防具',
                                action: () => enterShop(currentLocationName)
                            });
                            addInteractionOption(optionsContainer, {
                                icon: '🔨',
                                title: '修理装备',
                                description: '修复损坏的装备',
                                action: () => repairEquipment()
                            });
                            break;
                            
                        case 'potion_shop':
                            addInteractionOption(optionsContainer, {
                                icon: '🧪',
                                title: '购买药水',
                                description: '购买恢复药水和增益药剂',
                                action: () => enterShop(currentLocationName)
                            });
                            break;
                            
                        case 'research':
                            addInteractionOption(optionsContainer, {
                                icon: '📚',
                                title: '查阅书籍',
                                description: '研究魔法和技能知识',
                                action: () => researchBooks()
                            });
                            break;
                            
                        case 'combat_zone':
                            addInteractionOption(optionsContainer, {
                                icon: '🎯',
                                title: '寻找怪物',
                                description: '主动寻找怪物进行战斗',
                                action: () => startForestBattle()
                            });
                            break;
                            
                        case 'resource_gathering':
                        case 'exploration':
                            addInteractionOption(optionsContainer, {
                                icon: '�',
                                title: '采集资源',
                                description: '寻找有用的材料和资源',
                                action: () => collectHerbs()
                            });
                            break;
                            
                        case 'trade':
                            addInteractionOption(optionsContainer, {
                                icon: '🏪',
                                title: '交易',
                                description: '与商贩进行交易',
                                action: () => exploreArea()
                            });
                            break;
                    }
                });
                
                // 如果没有特殊功能，添加默认探索选项
                if (features.length === 0) {
                    addInteractionOption(optionsContainer, {
                        icon: '🚶',
                        title: '探索周围',
                        description: '查看这个地方有什么有趣的东西',
                        action: () => exploreArea()
                    });
                }
            }
        }
    } catch (error) {
        console.error('获取位置信息失败:', error);
        // 如果获取失败，添加默认选项
        addInteractionOption(optionsContainer, {
            icon: '🚶',
            title: '探索周围',
            description: '查看这个地方有什么有趣的东西',
            action: () => exploreArea()
        });
    }
    
    // 添加通用选项
    addInteractionOption(optionsContainer, {
        icon: '📋',
        title: '查看状态',
        description: '检查角色状态和装备',
        action: () => showCharacterStatus()
    });
}

// 添加互动选项
function addInteractionOption(container, option) {
    console.log('添加互动选项:', option.title, '到容器:', container);
    const optionElement = document.createElement('div');
    optionElement.className = 'interaction-option';
    optionElement.onclick = option.action;
    
    optionElement.innerHTML = `
        <div class="icon">${option.icon}</div>
        <div class="content">
            <div class="title">${option.title}</div>
            <div class="description">${option.description}</div>
        </div>
    `;
    
    container.appendChild(optionElement);
    console.log('已添加互动选项到容器');
}

// 触发互动事件
async function triggerInteractionEvent(eventId, interactionType) {
    console.log('触发互动事件:', eventId, '类型:', interactionType);
    
    try {
        switch (interactionType) {
            case 'shop':
                // 商店类型互动 - 打开商店界面
                const currentLocation = await getCurrentLocation();
                if (currentLocation && currentLocation.current_location) {
                    enterShop(currentLocation.current_location);
                }
                break;
                
            case 'fight':
                // 战斗类型互动 - 触发战斗事件
                const response = await makeAuthenticatedRequest(`${API_BASE_URL}/trigger_event`, {
                    method: 'POST',
                    body: JSON.stringify({
                        event_id: eventId
                    })
                });
                
                if (response && response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        showMessage(data.message || '开始战斗！', 'success');
                        // 如果是战斗事件，可能需要跳转到战斗界面
                        if (data.battle_started) {
                            // 处理战斗开始逻辑
                            console.log('战斗已开始');
                        }
                    } else {
                        showMessage(data.error || '无法触发事件', 'error');
                    }
                } else {
                    showMessage('请求失败', 'error');
                }
                break;
                
            case 'healing':
                // 恢复类型互动
                restAtHome();
                break;
                
            case 'repair':
                // 修理类型互动
                repairEquipment();
                break;
                
            case 'research':
                // 研究类型互动
                researchBooks();
                break;
                
            case 'gathering':
                // 采集类型互动
                collectHerbs();
                break;
                
            default:
                // 默认类型 - 通过API触发事件
                const defaultResponse = await makeAuthenticatedRequest(`${API_BASE_URL}/trigger_event`, {
                    method: 'POST',
                    body: JSON.stringify({
                        event_id: eventId
                    })
                });
                
                if (defaultResponse && defaultResponse.ok) {
                    const defaultData = await defaultResponse.json();
                    if (defaultData.success) {
                        showMessage(defaultData.message || '事件已触发！', 'success');
                    } else {
                        showMessage(defaultData.error || '无法触发事件', 'error');
                    }
                }
                break;
        }
    } catch (error) {
        console.error('触发互动事件失败:', error);
        showMessage('操作失败，请重试', 'error');
    }
}

// 隐藏所有内容区域
function hideAllContentAreas() {
    // 隐藏所有内容区域
    document.getElementById('defaultContent').style.display = 'none';
    document.getElementById('shopContentArea').style.display = 'none';
    document.getElementById('battleContentArea').style.display = 'none';
    document.getElementById('locationInteractionArea').style.display = 'none';
}

// 获取当前位置信息
async function getCurrentLocation() {
    try {
        const token = localStorage.getItem('sessionToken');
        if (!token) return null;
        
        const response = await makeAuthenticatedRequest(`${API_BASE_URL}/get_user_location`, {
            method: 'GET'
        });
        
        if (response.ok) {
            const data = await response.json();
            return data.success ? data.location : null;
        }
    } catch (error) {
        console.error('获取位置信息失败:', error);
    }
    return null;
}

// 触发村外森林哥布林战斗
// 在森林中主动寻找战斗
async function startForestBattle() {
    try {
        // 创建哥布林战斗实例
        const goblin = {
            name: '普通哥布林',
            avatar: '👹',
            hp: 30,
            maxHp: 30,
            attack: 8,
            defense: 3,
            exp: 15,
            gold: 5
        };
        
        showMessage('你在森林中遭遇了一只普通哥布林！', 'warning');
        startBattle(goblin);
        
    } catch (error) {
        console.error('森林战斗失败:', error);
        showMessage('森林战斗失败', 'error');
    }
}

// 检查可触发的事件
async function checkEvents() {
    try {
        const token = localStorage.getItem('sessionToken');
        if (!token) return;
        
        const response = await makeAuthenticatedRequest(`${API_BASE_URL}/api/events/check`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success && data.events.length > 0) {
            console.log('发现可触发事件:', data.events);
            
            // 随机选择一个事件触发（可以根据优先级改进）
            const randomEvent = data.events[Math.floor(Math.random() * data.events.length)];
            await handleEventTrigger(randomEvent);
        }
    } catch (error) {
        console.error('检查事件失败:', error);
    }
}

// 处理事件触发
async function handleEventTrigger(event) {
    try {
        console.log('触发事件:', event.name);
        
        // 根据事件类型处理
        if (event.event_type === 'battle') {
            // 战斗事件
            showMessage(`${event.name} - ${event.condition}`, 'warning');
            
            // 询问玩家是否参与战斗
            const participate = confirm(`遭遇事件：${event.name}\n${event.result}\n\n是否开始战斗？`);
            
            if (participate) {
                await startBattleFromEvent(event.event_id);
            }
        } else if (event.event_type === 'treasure') {
            // 宝藏事件
            showMessage(`发现宝藏：${event.name}`, 'success');
            await triggerEvent(event.event_id);
        } else {
            // 其他事件
            showMessage(`触发事件：${event.name}`, 'info');
            await triggerEvent(event.event_id);
        }
    } catch (error) {
        console.error('处理事件触发失败:', error);
    }
}

// 触发事件
async function triggerEvent(eventId) {
    try {
        const token = localStorage.getItem('sessionToken');
        const response = await fetch(`/api/events/trigger/${eventId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Session-Token': token
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('事件触发成功:', data);
            return data;
        } else {
            console.error('事件触发失败:', data.error);
        }
    } catch (error) {
        console.error('触发事件请求失败:', error);
    }
}

// 从事件开始战斗
async function startBattleFromEvent(eventId) {
    try {
        const token = localStorage.getItem('sessionToken');
        const response = await fetch(`/api/events/battle/${eventId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Session-Token': token
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            const battleData = data.battle_data;
            if (battleData.enemy) {
                startBattle(battleData.enemy);
            }
        } else {
            showMessage('战斗开始失败：' + data.error, 'error');
        }
    } catch (error) {
        console.error('从事件开始战斗失败:', error);
        showMessage('战斗开始失败', 'error');
    }
}

// 获取事件历史
async function getEventHistory() {
    try {
        const token = localStorage.getItem('sessionToken');
        const response = await fetch('/api/events/history?limit=10', {
            method: 'GET',
            headers: {
                'X-Session-Token': token
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('事件历史:', data.history);
            return data.history;
        }
    } catch (error) {
        console.error('获取事件历史失败:', error);
    }
}

// ======= 战斗系统 =======

let battleData = {
    inBattle: false,
    playerTurn: true,
    enemy: null,
    playerHp: 100,
    playerMaxHp: 100,
    playerMp: 50,
    playerMaxMp: 50,
    playerAttack: 10,
    playerDefense: 5
};

// 开始战斗
function startBattle(enemyData) {
    battleData.inBattle = true;
    battleData.playerTurn = true;
    battleData.enemy = enemyData;
    
    // 从用户数据获取玩家属性
    battleData.playerHp = parseInt(document.getElementById('userHP').textContent) || 100;
    battleData.playerMaxHp = battleData.playerHp;
    battleData.playerMp = parseInt(document.getElementById('userMP').textContent) || 50;
    battleData.playerMaxMp = battleData.playerMp;
    battleData.playerAttack = parseInt(document.getElementById('userAttack').textContent) || 10;
    battleData.playerDefense = parseInt(document.getElementById('userDefense').textContent) || 5;
    
    // 显示战斗界面
    showBattleContent();
    
    // 初始化战斗界面
    initBattleUI();
    
    // 添加战斗开始日志
    addBattleLog(`遭遇了 ${enemyData.name}！`, 'info');
    addBattleLog('战斗开始！', 'info');
}

// 初始化战斗界面
function initBattleUI() {
    // 设置敌人信息
    document.getElementById('enemyName').textContent = battleData.enemy.name;
    document.getElementById('enemyAvatar').textContent = battleData.enemy.avatar || '👹';
    
    // 设置玩家信息
    document.getElementById('battlePlayerName').textContent = document.getElementById('usernameDisplay').textContent || '玩家';
    
    // 更新血条和魔法条
    updateBattleUI();
    
    // 清空战斗日志
    document.getElementById('battleLog').innerHTML = '';
    
    // 设置回合指示器
    updateTurnIndicator();
}

// 更新战斗界面
function updateBattleUI() {
    // 更新敌人血条
    const enemyHpPercent = (battleData.enemy.hp / battleData.enemy.maxHp) * 100;
    document.getElementById('enemyHpFill').style.width = enemyHpPercent + '%';
    document.getElementById('enemyHpText').textContent = `${battleData.enemy.hp}/${battleData.enemy.maxHp}`;
    
    // 更新玩家血条
    const playerHpPercent = (battleData.playerHp / battleData.playerMaxHp) * 100;
    document.getElementById('playerHpFill').style.width = playerHpPercent + '%';
    document.getElementById('playerHpText').textContent = `${battleData.playerHp}/${battleData.playerMaxHp}`;
    
    // 更新玩家魔法条
    const playerMpPercent = (battleData.playerMp / battleData.playerMaxMp) * 100;
    document.getElementById('playerMpFill').style.width = playerMpPercent + '%';
    document.getElementById('playerMpText').textContent = `${battleData.playerMp}/${battleData.playerMaxMp}`;
}

// 更新回合指示器
function updateTurnIndicator() {
    const indicator = document.getElementById('turnIndicator');
    if (battleData.playerTurn) {
        indicator.textContent = '你的回合';
        enableBattleActions();
    } else {
        indicator.textContent = '敌人回合';
        disableBattleActions();
    }
}

// 启用战斗按钮
function enableBattleActions() {
    document.querySelectorAll('.battle-btn').forEach(btn => btn.disabled = false);
}

// 禁用战斗按钮
function disableBattleActions() {
    document.querySelectorAll('.battle-btn').forEach(btn => btn.disabled = true);
}

// 添加战斗日志
function addBattleLog(message, type = 'info') {
    const log = document.getElementById('battleLog');
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    entry.textContent = message;
    log.appendChild(entry);
    log.scrollTop = log.scrollHeight;
}

// 玩家攻击
function playerAttack() {
    if (!battleData.inBattle || !battleData.playerTurn) return;
    
    // 计算伤害（基础攻击力 + 随机值）
    const damage = Math.floor(battleData.playerAttack * (0.8 + Math.random() * 0.4));
    battleData.enemy.hp -= damage;
    
    addBattleLog(`你对 ${battleData.enemy.name} 造成了 ${damage} 点伤害！`, 'damage');
    
    // 检查敌人是否死亡
    if (battleData.enemy.hp <= 0) {
        battleData.enemy.hp = 0;
        updateBattleUI();
        endBattle(true);
        return;
    }
    
    // 切换到敌人回合
    battleData.playerTurn = false;
    updateBattleUI();
    updateTurnIndicator();
    
    // 敌人行动（延迟执行）
    setTimeout(enemyAction, 1500);
}

// 玩家防御
function playerDefend() {
    if (!battleData.inBattle || !battleData.playerTurn) return;
    
    addBattleLog('你采取了防御姿态！', 'info');
    
    // 防御状态（下次受到伤害减少50%）
    battleData.defending = true;
    
    // 切换到敌人回合
    battleData.playerTurn = false;
    updateTurnIndicator();
    
    // 敌人行动（延迟执行）
    setTimeout(enemyAction, 1500);
}

// 玩家逃跑
function playerFlee() {
    if (!battleData.inBattle || !battleData.playerTurn) return;
    
    // 逃跑成功率70%
    if (Math.random() < 0.7) {
        addBattleLog('你成功逃脱了！', 'info');
        endBattle(false);
    } else {
        addBattleLog('逃跑失败！', 'info');
        
        // 切换到敌人回合
        battleData.playerTurn = false;
        updateTurnIndicator();
        
        // 敌人行动（延迟执行）
        setTimeout(enemyAction, 1500);
    }
}

// 敌人行动
function enemyAction() {
    if (!battleData.inBattle) return;
    
    // 敌人攻击
    let damage = Math.floor(battleData.enemy.attack * (0.8 + Math.random() * 0.4));
    
    // 如果玩家在防御，伤害减半
    if (battleData.defending) {
        damage = Math.floor(damage * 0.5);
        battleData.defending = false;
        addBattleLog(`${battleData.enemy.name} 攻击了你，但被你的防御减弱了伤害！`, 'info');
    } else {
        addBattleLog(`${battleData.enemy.name} 攻击了你！`, 'info');
    }
    
    battleData.playerHp -= damage;
    addBattleLog(`你受到了 ${damage} 点伤害！`, 'damage');
    
    // 检查玩家是否死亡
    if (battleData.playerHp <= 0) {
        battleData.playerHp = 0;
        updateBattleUI();
        endBattle(false);
        return;
    }
    
    // 切换到玩家回合
    battleData.playerTurn = true;
    updateBattleUI();
    updateTurnIndicator();
}

// 结束战斗
function endBattle(victory) {
    battleData.inBattle = false;
    
    if (victory) {
        addBattleLog(`你击败了 ${battleData.enemy.name}！`, 'heal');
        addBattleLog(`获得了 ${battleData.enemy.exp || 10} 经验值！`, 'heal');
        
        // 这里可以添加奖励逻辑
        setTimeout(() => {
            showDefaultContent();
            showMessage('战斗胜利！', 'success');
        }, 2000);
    } else {
        if (battleData.playerHp <= 0) {
            addBattleLog('你被击败了...', 'damage');
            setTimeout(() => {
                showDefaultContent();
                showMessage('战斗失败！', 'error');
                // 这里可以添加失败惩罚逻辑
            }, 2000);
        } else {
            // 逃跑成功
            setTimeout(() => {
                showDefaultContent();
                showMessage('成功逃脱！', 'info');
            }, 1000);
        }
    }
}



// ======= 地图模态框功能 =======

let mapData = {
    areas: [],
    locations: [],
    currentArea: null
};

// 切换地图模态框
function toggleMapModal() {
    const modal = document.getElementById('mapModal');
    if (modal.style.display === 'none' || modal.style.display === '') {
        openMapModal();
    } else {
        closeMapModal();
    }
}

// 打开地图模态框
async function openMapModal() {
    const modal = document.getElementById('mapModal');
    modal.style.display = 'block';
    
    // 重置视图到区域选择
    showAreasView();
    
    // 加载地图数据
    await loadMapData();
    
    // 显示区域
    displayAreas();
}

// 关闭地图模态框
function closeMapModal() {
    const modal = document.getElementById('mapModal');
    modal.style.display = 'none';
}

// 加载地图数据
async function loadMapData() {
    try {
        // 获取用户当前位置
        const locationResponse = await makeAuthenticatedRequest(`${API_BASE_URL}/get_user_location`);
        let currentLocation = null;
        
        if (locationResponse) {
            const locationData = await locationResponse.json();
            if (locationData.success) {
                currentLocation = locationData.location;
            }
        }

        // 加载所有区域的地点
        const areas = [
            { id: 'novice_village', name: '新手村', icon: '🏘️', description: '安全的新手村落，适合初学者探索和学习' },
            { id: 'village_outskirts', name: '村庄外围', icon: '🌲', description: '新手村周围的危险区域，有各种怪物出没' }
        ];

        mapData.areas = areas;
        mapData.locations = [];

        // 加载每个区域的地点
        for (const area of areas) {
            const response = await makeAuthenticatedRequest(`${API_BASE_URL}/get_area_locations?area=${area.id}`);
            
            if (response) {
                const data = await response.json();
                if (data.success && data.locations) {
                    const locationsWithArea = data.locations.map(loc => ({
                        ...loc,
                        area_id: area.id,
                        area_name: area.name,
                        is_current: currentLocation && loc.location_name === currentLocation.current_location
                    }));
                    mapData.locations = mapData.locations.concat(locationsWithArea);
                }
            }
        }

        // 标记当前区域
        if (currentLocation) {
            mapData.areas = mapData.areas.map(area => ({
                ...area,
                is_current: area.id === currentLocation.current_area
            }));
        }

        console.log('地图数据加载完成:', mapData);
    } catch (error) {
        console.error('加载地图数据失败:', error);
        showMessage('加载地图数据失败', 'error');
    }
}

// 显示区域选择视图
function showAreasView() {
    document.getElementById('mapAreasView').style.display = 'block';
    document.getElementById('mapLocationsView').style.display = 'none';
}

// 显示地点选择视图
function showLocationsView(areaId, areaName) {
    mapData.currentArea = areaId;
    document.getElementById('mapAreasView').style.display = 'none';
    document.getElementById('mapLocationsView').style.display = 'block';
    document.getElementById('currentAreaName').textContent = areaName;
    
    displayLocations(areaId);
}

// 显示区域列表
function displayAreas() {
    const areasGrid = document.getElementById('areasGrid');
    areasGrid.innerHTML = '';

    mapData.areas.forEach(area => {
        const areaCard = document.createElement('div');
        areaCard.className = `area-card ${area.is_current ? 'current-area' : ''}`;
        areaCard.onclick = () => showLocationsView(area.id, area.name);

        areaCard.innerHTML = `
            <div class="area-icon">${area.icon}</div>
            <div class="area-name">${area.name}</div>
            <div class="area-desc">${area.description}</div>
            ${area.is_current ? '<div class="location-type-badge">当前区域</div>' : ''}
        `;

        areasGrid.appendChild(areaCard);
    });
}

// 显示指定区域的地点列表
function displayLocations(areaId) {
    const locationsGrid = document.getElementById('locationsGrid');
    locationsGrid.innerHTML = '';

    const areaLocations = mapData.locations.filter(loc => loc.area_id === areaId);

    if (areaLocations.length === 0) {
        locationsGrid.innerHTML = '<p>该区域暂无可访问的地点</p>';
        return;
    }

    areaLocations.forEach(location => {
        const locationCard = document.createElement('div');
        locationCard.className = `location-card ${location.location_type} ${location.is_current ? 'current-location' : ''}`;
        locationCard.onclick = () => selectLocation(location);

        // 根据地点类型选择图标
        let locationIcon = '📍';
        switch (location.location_type) {
            case 'shop':
                locationIcon = '🏪';
                break;
            case 'safe_zone':
                locationIcon = '🏠';
                break;
            case 'wilderness':
                locationIcon = '🌲';
                break;
            case 'commercial':
                locationIcon = '🏛️';
                break;
            default:
                locationIcon = '📍';
        }

        // 地点类型中文名
        const typeNames = {
            'shop': '商店',
            'safe_zone': '安全区',
            'wilderness': '野外',
            'commercial': '商业区'
        };

        locationCard.innerHTML = `
            <div class="location-icon">${locationIcon}</div>
            <div class="location-name-map">${location.display_name}</div>
            <div class="location-desc-map">${location.description || '暂无描述'}</div>
            <div class="location-type-badge">${typeNames[location.location_type] || location.location_type}</div>
            ${location.is_current ? '<div class="location-type-badge">当前位置</div>' : ''}
        `;

        locationsGrid.appendChild(locationCard);
    });
}

// 选择地点（仅显示信息，不实际移动）
function selectLocation(location) {
    if (location.is_current) {
        showMessage(`您已经在 ${location.display_name} 了`, 'info');
    } else {
        // 显示提示信息
        const message = `要前往 ${location.display_name}，请对主持人说："我想去${location.display_name}"`;
        showMessage(message, 'info');
        
        // 可选：关闭地图
        closeMapModal();
    }
}

// 点击模态框背景关闭
document.addEventListener('click', function(event) {
    const modal = document.getElementById('mapModal');
    if (event.target === modal) {
        closeMapModal();
    }
});

// ======= 位置互动功能实现 =======

// 开始与木偶假人战斗
async function startTrainingDummyBattle() {
    try {
        const response = await makeAuthenticatedRequest(`${API_BASE_URL}/api/training/dummy-battle`, {
            method: 'POST'
        });
        
        if (!response) return;
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
            
            // 如果触发了战斗，显示战斗界面
            if (data.battle_triggered && data.battle_data) {
                hideAllContentAreas();
                startBattle(data.battle_data.enemy);
            }
        } else {
            showMessage(data.error, 'error');
        }
    } catch (error) {
        console.error('开始假人战斗失败:', error);
        showMessage('开始假人战斗失败', 'error');
    }
}

// 在家休息恢复
async function restAtHome() {
    showMessage('💤 你在家中好好休息了一下...', 'info');
    
    // 这里可以添加实际的恢复逻辑
    setTimeout(() => {
        showMessage('✨ 生命值和法力值已恢复！', 'success');
    }, 2000);
}

// 进入商店
async function enterShop(shopType) {
    console.log('🏪 进入商店:', shopType);
    hideAllContentAreas();
    
    // 显示商店界面
    const shopEl = document.getElementById('shopContentArea');
    shopEl.style.removeProperty('display');
    shopEl.style.display = 'flex';
    console.log('✅ 商店界面已显示');
    
    // 根据商店类型加载不同的商品
    if (shopType === 'blacksmith') {
        loadShopItems('铁匠铺');  // 使用数据库中的商店名称
        document.getElementById('dynamicShopName').textContent = '🔨 铁匠铺';
        document.getElementById('dynamicShopDesc').textContent = '购买武器和防具';
    } else if (shopType === 'potion_shop') {
        loadShopItems('药剂师');  // 使用数据库中的商店名称
        document.getElementById('dynamicShopName').textContent = '🧪 药水店';
        document.getElementById('dynamicShopDesc').textContent = '购买恢复药水和增益药剂';
    } else if (shopType === 'library') {
        loadShopItems('药剂师');  // 使用数据库中的商店名称
        document.getElementById('dynamicShopName').textContent = '📚 图书馆·药剂师';
        document.getElementById('dynamicShopDesc').textContent = '购买恢复药水和增益药剂';
    }
    
    showMessage(`欢迎光临！`, 'success');
}

// 退出商店
function exitShop() {
    console.log('🚪 退出商店');
    // 检查并显示当前位置对应的内容
    checkAndShowLocationContent();
}

// 修理装备
async function repairEquipment() {
    showMessage('🔧 装备修理功能即将推出...', 'info');
}

// 采集草药
async function collectHerbs() {
    showMessage('🌿 你在森林中寻找草药...', 'info');
    
    setTimeout(() => {
        const herbs = ['普通草药', '治疗草', '魔法草'];
        const foundHerb = herbs[Math.floor(Math.random() * herbs.length)];
        showMessage(`✨ 你找到了 ${foundHerb}！`, 'success');
    }, 2000);
}

// 探索区域
async function exploreArea() {
    showMessage('🔍 你仔细探索了周围...', 'info');
    
    setTimeout(() => {
        const discoveries = [
            '你发现了一些有趣的痕迹',
            '你找到了几枚铜币',
            '你注意到了一些不寻常的东西',
            '你感受到了周围的平静'
        ];
        const discovery = discoveries[Math.floor(Math.random() * discoveries.length)];
        showMessage(`👁️ ${discovery}`, 'info');
    }, 2000);
}

// 显示角色状态
async function showCharacterStatus() {
    hideAllContentAreas();
    showMessage('📊 角色状态信息已在左侧面板显示', 'info');
}

// 查阅书籍
async function researchBooks() {
    showMessage('📖 你仔细研读图书馆的书籍...', 'info');
    
    setTimeout(() => {
        const knowledge = [
            '你学到了一些基础魔法知识',
            '你了解了怪物的弱点',
            '你掌握了一些战斗技巧',
            '你获得了草药学知识'
        ];
        const learned = knowledge[Math.floor(Math.random() * knowledge.length)];
        showMessage(`📚 ${learned}`, 'success');
    }, 2000);
}

/* 移除了返回相关的函数 */
