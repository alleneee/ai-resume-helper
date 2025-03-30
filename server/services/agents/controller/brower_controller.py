from typing import Optional, Dict, Any, List
from browser_use import Controller, ActionResult, Browser

# 初始化控制器
controller = Controller()

# -------------------- 基本浏览器操作 --------------------

@controller.action('向用户请求信息')
def ask_human(question: str) -> ActionResult:
    """向用户请求输入信息"""
    answer = input(f'\n{question}\n输入: ')
    return ActionResult(extracted_content=answer)

@controller.action('保存屏幕截图')
async def save_screenshot(browser, file_name: str) -> ActionResult:
    """保存当前页面的屏幕截图"""
    await browser.screenshot(path=file_name)
    return ActionResult(extracted_content=f"屏幕截图已保存为{file_name}")

@controller.action('获取页面内容')
async def get_page_content(browser) -> ActionResult:
    """获取当前页面的HTML内容"""
    content = await browser.content()
    return ActionResult(
        include_in_memory=True,
        extracted_content=content
    )

@controller.action('打开网页')
async def navigate_to(browser, url: str) -> ActionResult:
    """导航到指定URL"""
    await browser.goto(url)
    return ActionResult(extracted_content=f"已成功导航到 {url}")

@controller.action('获取当前URL')
async def get_current_url(browser) -> ActionResult:
    """获取当前页面URL"""
    url = browser.url
    return ActionResult(extracted_content=url)

@controller.action('关闭浏览器')
async def close_browser(browser) -> ActionResult:
    """关闭浏览器实例"""
    await browser.close()
    return ActionResult(extracted_content="浏览器已关闭")

# -------------------- 页面交互操作 --------------------

@controller.action('点击元素')
async def click_element(browser, selector: str) -> ActionResult:
    """点击指定的页面元素"""
    await browser.click(selector)
    return ActionResult(extracted_content=f"已点击元素 {selector}")

@controller.action('填写表单字段')
async def fill_form_field(browser, selector: str, value: str) -> ActionResult:
    """在表单字段中填入内容"""
    await browser.fill(selector, value)
    return ActionResult(extracted_content=f"已在 {selector} 填入 {value}")

@controller.action('提交表单')
async def submit_form(browser, selector: str) -> ActionResult:
    """提交指定的表单"""
    await browser.press(selector, "Enter")
    return ActionResult(extracted_content=f"已提交表单 {selector}")

@controller.action('选择下拉选项')
async def select_option(browser, selector: str, value: str) -> ActionResult:
    """在下拉菜单中选择选项"""
    await browser.select_option(selector, value)
    return ActionResult(extracted_content=f"已在 {selector} 选择 {value}")

@controller.action('按下键盘按键')
async def press_key(browser, selector: str, key: str) -> ActionResult:
    """在指定元素上按下键盘按键"""
    await browser.press(selector, key)
    return ActionResult(extracted_content=f"已在 {selector} 按下 {key} 键")

# -------------------- 数据提取操作 --------------------

@controller.action('提取文本内容')
async def extract_text(browser, selector: str) -> ActionResult:
    """提取指定元素的文本内容"""
    text = await browser.text_content(selector)
    return ActionResult(extracted_content=text)

@controller.action('提取属性值')
async def extract_attribute(browser, selector: str, attribute: str) -> ActionResult:
    """提取指定元素的属性值"""
    value = await browser.get_attribute(selector, attribute)
    return ActionResult(extracted_content=value)

@controller.action('提取多个元素')
async def extract_multiple_elements(browser, selector: str) -> ActionResult:
    """提取页面中多个元素的内容"""
    elements = await browser.query_selector_all(selector)
    results = []
    for element in elements:
        text = await element.text_content()
        results.append(text)
    return ActionResult(extracted_content=results)

@controller.action('提取表格数据')
async def extract_table_data(browser, table_selector: str) -> ActionResult:
    """提取HTML表格的数据"""
    rows = await browser.query_selector_all(f"{table_selector} tr")
    table_data = []
    
    for row in rows:
        cells = await row.query_selector_all("td, th")
        row_data = []
        for cell in cells:
            text = await cell.text_content()
            row_data.append(text.strip())
        if row_data:
            table_data.append(row_data)
            
    return ActionResult(extracted_content=table_data)

@controller.action('评估JavaScript')
async def evaluate_javascript(browser, script: str) -> ActionResult:
    """执行JavaScript代码并返回结果"""
    result = await browser.evaluate(script)
    return ActionResult(extracted_content=result)

# -------------------- 辅助功能 --------------------

@controller.action('等待元素可见')
async def wait_for_element(browser, selector: str, timeout: int = 30000) -> ActionResult:
    """等待元素在页面上可见"""
    await browser.wait_for_selector(selector, timeout=timeout)
    return ActionResult(extracted_content=f"元素 {selector} 已可见")

@controller.action('等待导航完成')
async def wait_for_navigation(browser) -> ActionResult:
    """等待页面导航完成"""
    await browser.wait_for_load_state("networkidle")
    return ActionResult(extracted_content="页面导航已完成")

@controller.action('等待特定时间')
async def wait_timeout(browser, milliseconds: int) -> ActionResult:
    """等待指定的毫秒数"""
    await browser.wait_for_timeout(milliseconds)
    return ActionResult(extracted_content=f"已等待 {milliseconds} 毫秒")

@controller.action('重新加载页面')
async def reload_page(browser) -> ActionResult:
    """重新加载当前页面"""
    await browser.reload()
    return ActionResult(extracted_content="页面已重新加载")

# -------------------- 职位搜索专用操作 --------------------

@controller.action('搜索职位')
async def search_jobs(browser, keywords: str, location: str = None) -> ActionResult:
    """在招聘网站上搜索职位"""
    # 假设我们已经在招聘网站上
    if location:
        # 选择地点
        await browser.click("选择地点的选择器")
        await browser.fill("地点输入框选择器", location)
        await browser.click("地点确认按钮选择器")
    
    # 输入关键词并搜索
    await browser.fill("关键词输入框选择器", keywords)
    await browser.click("搜索按钮选择器")
    
    # 等待搜索结果加载
    await browser.wait_for_selector("搜索结果列表选择器")
    
    return ActionResult(extracted_content="职位搜索已完成")

@controller.action('提取职位列表')
async def extract_job_listings(browser, limit: int = 5) -> ActionResult:
    """提取搜索结果中的职位列表"""
    # 获取职位列表元素
    job_elements = await browser.query_selector_all("职位列表项选择器")
    
    results = []
    for i, job_element in enumerate(job_elements):
        if i >= limit:
            break
            
        # 提取职位信息
        title = await job_element.query_selector("职位标题选择器")
        company = await job_element.query_selector("公司名称选择器")
        salary = await job_element.query_selector("薪资选择器")
        location = await job_element.query_selector("地点选择器")
        
        job_data = {
            "title": await title.text_content() if title else "未知职位",
            "company_name": await company.text_content() if company else "未知公司",
            "salary_range": await salary.text_content() if salary else "薪资面议",
            "location": await location.text_content() if location else "未知地点",
            "url": await job_element.get_attribute("链接选择器", "href") if await job_element.query_selector("链接选择器") else "#"
        }
        
        results.append(job_data)
    
    return ActionResult(extracted_content=results)

@controller.action('获取职位详情')
async def get_job_details(browser, job_url: str) -> ActionResult:
    """获取职位详情页的信息"""
    # 导航到职位详情页
    await browser.goto(job_url)
    await browser.wait_for_load_state("networkidle")
    
    # 提取职位详细信息
    details = {
        "title": await browser.text_content("职位标题选择器"),
        "company_name": await browser.text_content("公司名称选择器"),
        "salary_range": await browser.text_content("薪资选择器"),
        "location": await browser.text_content("地点选择器"),
        "experience_level": await browser.text_content("经验要求选择器"),
        "education_level": await browser.text_content("学历要求选择器"),
        "job_description": await browser.text_content("职位描述选择器"),
        "responsibilities": await browser.text_content("职责选择器"),
        "requirements": await browser.text_content("要求选择器"),
        "company_description": await browser.text_content("公司描述选择器")
    }
    
    return ActionResult(extracted_content=details)