// 修复后的互动选项更新函数

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
                
                // 根据配置的互动选项动态添加
                interactions.forEach(interaction => {
                    const interactionOption = {
                        title: interaction.interaction_name,
                        description: `进行${interaction.interaction_name}`,
                        action: () => triggerInteractionEvent(interaction.event_id, interaction.interaction_type)
                    };
                    
                    // 根据互动类型设置图标
                    switch (interaction.interaction_type) {
                        case 'shop':
                            interactionOption.icon = '🛒';
                            interactionOption.description = `打开${interaction.interaction_name}界面`;
                            break;
                        case 'fight':
                            interactionOption.icon = '⚔️';
                            interactionOption.description = `开始${interaction.interaction_name}`;
                            break;
                        case 'healing':
                            interactionOption.icon = '💤';
                            break;
                        case 'repair':
                            interactionOption.icon = '🔨';
                            break;
                        case 'research':
                            interactionOption.icon = '📚';
                            break;
                        case 'gathering':
                            interactionOption.icon = '🌿';
                            break;
                        default:
                            interactionOption.icon = '🎯';
                    }
                    
                    addInteractionOption(optionsContainer, interactionOption);
                });
                
                // 如果没有配置的互动，添加默认探索选项
                if (interactions.length === 0) {
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
