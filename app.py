import streamlit as st
import openai
import json

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

with open('agent_config.json', 'r', encoding='utf-8') as f:
    agent_config = json.load(f)

DEFAULT_CLIENT_TEXT = "Hello, I would like to update my budget to 180 euros please. My email is client@example.com. I would also like to change my delivery address to 123 Willy Wonka Street, Paris. Finally, I would like to change my license plate to ABC 123. Thank you in advance!"
TOOL_DEFINITIONS = {
    tool["name"]: tool
    for tool in agent_config.get("tools", [])
}

prompt_instructions = (
    "You are an assistant receiving an message. Your role is to extract the relevant details from the email and structure them. "
    "Generate a JSON object with a 'tools' key containing a list of objects. "
    "Each object must follow exactly this structure: "
    "{'name': 'field_name', 'function': 'function_name_to_call', 'type': 'number' or 'text', 'value': value_extracted_from_the_email}. "
    "The last element must be the response message for the customer with 'name': 'Response Message', written in a polite and professional tone. "
    f"Here is the list of available functions: {agent_config.get('tools', [])}. Warning: you must only use the listed functions and must not invent any new ones. "
    "If a request does not clearly match one of the functions, ignore it and do not include it in the final JSON."
)

@st.cache_data
def generate(ai_proposal, prompt_instructions):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "system",
            "content": prompt_instructions,
        }, {"role": "user", "content": ai_proposal}],
        response_format={ "type": "json_object" }
    )
    return json.loads(response.choices[0].message.content)

def main():

    st.set_page_config(page_title="Human Validation Interface", layout="wide")
    st.title("AI Validation Gateway")

    if "client_text" not in st.session_state:
        st.session_state.client_text = DEFAULT_CLIENT_TEXT

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        with st.container(border=True):
            st.subheader("Original Message")
            st.caption("Paste or edit the customer's message, then generate the validation proposal.")

            with st.form("customer_message_form"):
                edited_client_text = st.text_area(
                    "Message content",
                    value=st.session_state.client_text,
                    height=260
                )
                generate_clicked = st.form_submit_button("Generate Validation Proposal", use_container_width=True)

            if generate_clicked:
                st.session_state.client_text = edited_client_text

    with st.spinner("Generating the interface with OpenAI..."):
        ui_schema = generate(st.session_state.client_text, prompt_instructions)

    tools = ui_schema.get("tools", [])

    response_tool = None
    for tool in tools:
        if tool.get("name") == "Response Message":
            response_tool = tool
            break

    with col2:
        with st.container(border=True):
            st.subheader("Validation Panel")
            st.caption("Review each extracted action before sending it")
            st.subheader("Tools to Validate")
            final_edits = {}
            for tool in tools:
                field_name = tool['name']
                function_name = tool.get("function") or field_name
                tool_definition = TOOL_DEFINITIONS.get(function_name) or TOOL_DEFINITIONS.get(field_name, {})
                display_label = tool_definition.get("label", field_name)
                description = tool_definition.get("description")

                if field_name == 'Response Message':
                    continue

                with st.container(border=True):
                    st.markdown(f"**{display_label}**")

                    if description:
                        st.caption(description)

                    if tool['type'] == "number":
                        field_value = st.number_input(display_label, value=tool.get('value', 0.0), key=f"value_{function_name}")
                    else:
                        field_value = st.text_input(display_label, value=tool.get('value', ""), key=f"value_{function_name}")

                    decision = st.radio(
                        f"Decision for {display_label}",
                        options=["Approve", "Reject"],
                        index=0,
                        horizontal=True,
                        key=f"decision_{function_name}"
                    )

                    if decision == "Approve":
                        final_edits[field_name] = field_value

            st.subheader("Final Message")
            final_message = st.text_area(
                "Response message for the customer",
                value=(response_tool or {"value": "no answer"}).get('value', ""),
                height=150
            )
            message_decision = st.radio(
                "Decision for the final message",
                options=["Approve", "Reject"],
                index=0,
                horizontal=True,
                key="decision_response_message"
            )

    st.divider()
    if st.button("APPROVE AND SEND", use_container_width=True):
        st.success("Data sent to production!")
        payload = {"tools": final_edits}

        if message_decision == "Approve":
            payload["message"] = final_message

        st.json(payload)

if __name__ == "__main__":
    main()
