# Project Overview - Real War

Tài liệu này tóm tắt cấu trúc dự án Real War ở mức source-level, tập trung vào gameplay `CrowdBattle`.
Nguồn đối chiếu chính: `Assets/_Game/Docs/GDD/So_do_luong_logic_CrowdBattle.md` và các script trong
`Assets/_Game/Scripts/Gameplay/CrowdBattle/`.

Các nội dung runtime như Play Mode, profiler, build và cân bằng level chưa được xác minh trong tài liệu này.

## 1. Mục tiêu dự án

Real War là game Unity có gameplay chính dạng crowd runner battle:

- Người chơi điều khiển một đám đông trên lane.
- Đám đông tự bắn vào enemy, gate, barrel, gear và boss.
- Số lượng unit, damage, fire rate và income thay đổi qua upgrade trước trận và reward trong trận.
- Level được author bằng `ScriptableObject`, có thể đổi kịch bản qua Firebase Remote Config.
- Presentation ưu tiên batch/instancing/pool thay vì tạo nhiều `GameObject` runtime.

## 2. Cấu trúc thư mục chính

| Đường dẫn | Vai trò |
| --- | --- |
| `Assets/_Game/Scripts/Gameplay/CrowdBattle/` | Module gameplay CrowdBattle: config, runtime, simulation, event, presentation, upgrade và editor tool. |
| `Assets/_Game/Scripts/Gameplay/` | Bootstrap scene gameplay, environment, input chung, animation helper và marker. |
| `Assets/_Game/Scripts/Ads/` | Policy quảng cáo trong flow gameplay. |
| `Assets/_Game/Scripts/Effects/` | Effect dùng chung như fly effect, button effect. |
| `Assets/_Game/Configs/` | `ScriptableObject` cấu hình level, scenario, visual, bullet, reward và upgrade icon. |
| `Assets/_Game/Docs/GDD/` | Tài liệu thiết kế và luồng logic gameplay. |
| `Assets/_FrameWork/` | Hạ tầng dùng lại của project, không chứa logic gameplay đặc thù. |

## 3. Module CrowdBattle

```text
CrowdBattleGameplayManager
        |
        v
CrowdBattleRuntime
        |
        v
CrowdBattleSimulation
        |
        +-> CrowdFormationSolver
        +-> EnemyWaveSystem
        +-> CrowdCombatSystem
        +-> BossSystem
        +-> MultiplierGateSystem
        +-> BreakableObjectSystem
        +-> CrowdBattleEventBuffer
        |
        v
Presentation / UI / VFX / SFX / Tracking
```

### `Runtime`

`CrowdBattleRuntime` giữ state machine:

```text
PreBattle -> Running -> Won
                    \-> Lost
```

Runtime chạy fixed tick bằng `fixedTickRate`, giới hạn tick bù bằng `maxTicksPerFrame`, gom event từ
simulation thành `FrameEvents` cho rendered frame.

### `Simulation`

`CrowdBattleSimulation` là nguồn state gameplay. Mỗi fixed tick xử lý theo thứ tự:

```text
Input targetX
-> cập nhật CenterX và WorldDistance
-> cập nhật formation
-> chuẩn bị target gate
-> combat bullet / damage / collision
-> boss attack
-> gate apply
-> breakable reward
-> refresh target count
-> kiểm tra Won / Lost
```

Simulation dùng `NativeArray` cho unit, formation, bullet, target và DPS bucket. Đây là hướng data-oriented để
tránh tạo entity bằng `GameObject` trong hot path.

### `Presentation`

Các presenter đọc state/event từ runtime:

- `CrowdBattleInstancedPresenter`: vẽ bullet, marker gate/barrel/gear và cull theo khoảng nhìn.
- `CrowdBattleAnimationInstancingPresenter`: pool và đồng bộ visual ally/enemy.
- `BossPresenter`: tạo một boss prefab, phát animation attack/death và báo `NotifyBossHidden()`.
- `CrowdBattleEffectManager`: phát VFX/SFX từ event.
- `CrowdBattleProgressPresenter` và `CrowdBattleDebugHud`: UI runtime/debug.

Presentation không quyết định gameplay. Nó chỉ đọc state hoặc phản hồi event.

## 4. Dữ liệu level và scenario

### Config mode

`CrowdBattleConfig` là config cấp mode, chứa:

- danh sách level mặc định: `LevelConfigs`;
- danh sách scenario preset: `scenarioPresets`;
- thông số movement, crowd, projectile, combat, enemy, runtime và rendering budget.

Config runtime quan trọng:

| Field | Ý nghĩa |
| --- | --- |
| `crowdHardCap` | Sức chứa tối đa của crowd và buffer unit. |
| `initialUnitCount` | Số unit đầu trận. |
| `fixedTickRate` | Tần số fixed tick simulation. |
| `maxTicksPerFrame` | Giới hạn tick bù khi frame chậm. |
| `maxActiveBullets` | Sức chứa bullet runtime. |
| `maxCombatTargets` | Sức chứa target enemy/gate/object/boss. |
| `maxEventsPerTick` | Sức chứa event mỗi tick. |
| `visibleAheadDistance`, `visibleBehindDistance` | Khoảng cull presentation, không ảnh hưởng simulation. |

### Config level

`CrowdBattleLevelConfig` là config cấp level, chứa:

- `environment`: scene và lighting profile cho level.
- `enemyWaves`: enemy spawn theo distance.
- `gates`: gate Add/Multiply theo slot.
- `breakableObjects`: Barrel/Gear và reward.
- `bossDefinition`: boss duy nhất của level nếu `enabled`.

Trước khi runtime allocate buffer, `ValidateForRuntime()` kiểm tra dữ liệu level và giới hạn
`maxCombatTargets`.

### Scenario A/B

Level có thể được chọn bằng Firebase Remote Config:

```text
Firebase Remote Config: crowd_battle_scenario
        |
        v
CrowdBattleConfig.ResolveLevelConfig(scenarioId, stageIndex)
        |
        +-> nếu scenario hợp lệ: dùng preset tương ứng
        +-> nếu scenario rỗng/không hợp lệ: fallback `LevelConfigs`
        +-> stageIndex là 1-based, level index là 0-based và loop theo số level
```

Client không random lại nhóm A/B. Firebase quyết định scenario.

## 5. Scene và environment

`GameplaySceneBootstrapManager` load environment additive theo `GameplayEnvironmentConfig`.

Luồng chính:

```text
Gameplay scene loaded
-> lấy stage hiện tại từ CrowdBattleUpgradePlayerPrefsRepository
-> resolve CrowdBattleLevelConfig
-> LoadEnvironment(environment)
-> apply object override
-> apply lighting profile
-> unload environment cũ nếu cần
```

Scene gameplay chính giữ logic runtime. Environment được load/unload riêng để đổi cảnh theo level mà không đổi
toàn bộ gameplay scene.

## 6. Combat và target

`CrowdCombatSystem` quản lý:

- bullet runtime;
- target registry;
- hit detection;
- damage trực tiếp cho enemy/boss;
- DPS bucket cho gate/barrel/gear.

Các loại target chính:

| `TargetKind` | Xử lý |
| --- | --- |
| `Enemy` | Nhận damage trực tiếp, có collision giảm unit. |
| `GateSlot` | Nhận DPS bucket, cập nhật value/width, apply khi crowd chạm. |
| `Barrel` | Nhận DPS bucket, phá để nhận reward. |
| `GearTier` | Nhận DPS bucket theo tier, phá để nhận reward. |
| `Boss` | Nhận damage trực tiếp, chết thì mở điều kiện thắng. |

`movementGroupId` và `lockAtLocalZ` cho phép nhiều target cùng nhóm dừng/tiếp tục di chuyển theo lock source.

## 7. Boss

Boss chỉ tồn tại khi `bossDefinition.enabled`.

Luồng boss:

```text
Reset
-> AddBossTarget
-> BossPhase.Approaching
-> tới attackDistance thì khóa scroll
-> BossPhase.Attacking / Cooldown
-> weaponHitbox overlap ally thì giết một phần crowd
-> boss health <= 0
-> BossPhase.Dead
-> BossDied event
-> BossPresenter phát animation chết
-> NotifyBossHidden()
-> runtime chuyển Won
```

Boss là target damage trực tiếp. Boss không dùng DPS bucket như gate, barrel hoặc gear.

## 8. Upgrade, economy và tracking

Upgrade trước trận dùng các class:

- `CrowdBattleUpgradePlayerPrefsRepository`: load/save trạng thái upgrade.
- `CrowdBattleUpgradeService`: mua upgrade bằng Gold/Gem, chuyển stage, complete stage.
- `CrowdBattleUpgradeCalculator`: tính level, cost, phase và snapshot stat đầu trận.
- `CrowdBattleUpgradeTrackingEvents`: tracking event cho upgrade card.

`CrowdBattleGameplayManager` tạo snapshot upgrade khi initialize runtime, rồi truyền vào simulation.
Khi upgrade hoàn tất trong UI, manager load lại state, build snapshot mới và apply vào simulation.

Economy trong trận:

- Enemy chết cộng Gold theo `baseGoldPerEnemy * effectiveIncomeRate`.
- Boss chết cộng Gold theo `baseGoldReward * effectiveIncomeRate`.
- Gold được cộng qua `DataManager.ChangeGold`.

Tracking gameplay:

- Start battle tạo `CurrentPlayId` mới.
- `UserBehaviorTracker.SendStartGameTracking` gửi stage, attempt, mode, flow và số character đầu trận.
- Khi thắng/thua/quit, `SendEndGameTracking` gửi result, fail reason, duration, progress và character number.

## 9. Ads policy

`FakeWarAdsPolicy` nhận tín hiệu từ gameplay manager:

- `NotifyRapidInput()` khi người chơi input liên tục trong `Running`.
- `TickGameplay(deltaTime)` trong khi trận đang chạy.
- `OnBattleStarted()` khi bắt đầu trận.
- `OnBattleCompleted()` khi trận kết thúc.

Chi tiết rule quảng cáo nằm trong `Assets/_Game/Scripts/Ads/FakeWarAdsPolicy.cs`.

## 10. Nguyên tắc mở rộng

Khi thêm hoặc sửa gameplay CrowdBattle:

- Ưu tiên thêm dữ liệu vào `CrowdBattleLevelConfig` hoặc `CrowdBattleConfig` nếu là thông số cân bằng.
- Giữ simulation tách khỏi presentation.
- Không tạo `GameObject`, `GetComponent`, `Find`, `Instantiate`, `Destroy`, LINQ hoặc closure trong hot path gameplay.
- Tôn trọng `crowdHardCap`, `maxActiveBullets`, `maxCombatTargets`, `maxEventsPerTick`.
- Với render số lượng lớn, dùng instancing/pool và nhớ giới hạn `Graphics.DrawMeshInstanced` là 1023 instance mỗi draw call.
- Event gameplay nên đi qua `CrowdBattleEventBuffer`; UI/VFX/SFX đọc event ở layer presentation.
- Khi thêm IAP/shop/popup mới, phải nối đủ `iap_show` -> `iap_action` -> `iap_purchase` với cùng `iap_session_id`.
- Không đưa logic gameplay đặc thù vào `Assets/_FrameWork`.

## 11. Tài liệu liên quan

| Tài liệu | Nội dung |
| --- | --- |
| `Assets/_Game/Docs/GDD/So_do_luong_logic_CrowdBattle.md` | Luồng source-level chi tiết của module CrowdBattle. |
| `Assets/_Game/Docs/GDD/Luong_logic_upgrade_cards_GDD.md` | Luồng logic upgrade card. |
| `Assets/_Game/Docs/GDD/Giai_thich_Crowd_fields_CrowdBattleConfig.md` | Giải thích field config CrowdBattle. |
| `Assets/_Game/Docs/GDD/FakeWar - GDD Crowd Mechanic.md` | Thiết kế mechanic crowd. |
| `Assets/_Game/Docs/GDD/FakeWar - GDD Gate .md` | Thiết kế gate. |
| `Assets/_Game/Docs/GDD/FakeWar - GDD Barel_Gear.md` | Thiết kế barrel/gear. |
| `Assets/_Game/Docs/GDD/FAKE WAR GDD_ CAMPAIGN BOSS MECHANICS.md` | Thiết kế boss campaign. |
| `Assets/_Game/Docs/GDD/FakeWar Ads Logic.md` | Logic ads. |
