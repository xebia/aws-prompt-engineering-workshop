import os
from typing import List

import boto3
import click
import random
import string
import csv
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors


def get_usernames(cloudformation, stack_name):
    resources = []
    paginator = cloudformation.get_paginator("list_stack_resources")
    for page in paginator.paginate(StackName=stack_name):
        resources.extend(page["StackResourceSummaries"])

    nested_stacks = [
        r for r in resources if r["ResourceType"] == "AWS::CloudFormation::Stack"
    ]
    usernames = []
    for r in nested_stacks:
        nested_stack_id = r.get("PhysicalResourceId")
        if nested_stack_id:
            try:
                desc = cloudformation.describe_stacks(StackName=nested_stack_id)
                stack_params = desc["Stacks"][0].get("Parameters", [])
                for param in stack_params:
                    if param["ParameterKey"] == "Username":
                        usernames.append(param["ParameterValue"])
            except Exception as e:
                print(
                    f"  Could not retrieve parameters for stack {nested_stack_id}: {e}"
                )
    return sorted(usernames)


def create_console_credentials(iam, username):
    iam.get_user(UserName=username)

    # Generate a random password with at least one number and one symbol
    length = 8
    letters = string.ascii_letters
    digits = string.digits
    symbols = "@#$"
    # Ensure at least one digit and one symbol
    password_chars = [
        random.choice(letters),
        random.choice(digits),
        random.choice(symbols),
    ]
    # Fill the rest with random choices from all sets
    all_chars = letters + digits + symbols
    password_chars += [
        random.choice(all_chars) for _ in range(length - len(password_chars))
    ]
    random.shuffle(password_chars)
    password = "".join(password_chars)
    try:
        iam.create_login_profile(
            UserName=username, Password=password, PasswordResetRequired=False
        )
        print(f"Created console password for {username}.")
    except iam.exceptions.EntityAlreadyExistsException:
        print(f"Login profile for {username} already exists.")

    return {
        "User name": username,
        "Password": password,
    }


def render_pdf(credentials: List[dict]) -> None:
    pdf_file = "credentials.pdf"
    c = canvas.Canvas(pdf_file, pagesize=A4)
    width, height = A4
    margin = 15 * mm
    box_height = (height - 2 * margin) / 10  # 10 boxes per page
    box_width = width - 2 * margin
    font_size = 12
    top_padding = 18  # Padding from top of box to first line
    line_spacing = 22  # Space between lines
    for idx, cred in enumerate(credentials):
        box_idx = idx % 10
        if box_idx == 0 and idx != 0:
            c.showPage()
        y_top = height - margin - box_idx * box_height
        x_left = margin
        # Draw box
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.rect(x_left, y_top - box_height, box_width, box_height, stroke=1, fill=0)
        # Write credentials with proper padding
        c.setFont("Helvetica-Bold", font_size)
        c.drawString(
            x_left + 10, y_top - top_padding, f"User name: {cred['User name']}"
        )
        c.setFont("Helvetica", font_size)
        c.drawString(
            x_left + 10,
            y_top - top_padding - line_spacing,
            f"Password: {cred['Password']}",
        )
        # Print label and URL on the same line
        c.setFont("Helvetica", font_size)
        label = "Console sign-in URL: "
        label_x = x_left + 10
        label_y = y_top - top_padding - 2 * line_spacing
        c.drawString(label_x, label_y, label)
        c.setFont("Helvetica-Oblique", font_size)
        url_x = label_x + c.stringWidth(label, "Helvetica", font_size) + 5
        c.drawString(url_x, label_y, cred["Console sign-in URL"])
    c.save()
    print(f"PDF with credentials written to {pdf_file}")


@click.command()
@click.option("--stack-name", required=True, help="Name of the CloudFormation stack")
@click.option(
    "--profile",
    default=lambda: os.environ.get("AWS_PROFILE", None),
    show_default="AWS_PROFILE env var",
    help="AWS profile name",
)
@click.option(
    "--region",
    default=lambda: os.environ.get("AWS_REGION", None),
    show_default="AWS_REGION env var",
    help="AWS region name",
)
@click.option(
    "--delete",
    is_flag=True,
    default=False,
    help="Delete IAM users and their login profiles for detected usernames",
)
def main(stack_name, profile, region, delete):
    session = boto3.session.Session(profile_name=profile, region_name=region)
    cloudformation = session.client("cloudformation")
    iam = session.client("iam")
    sts = session.client("sts")
    account_id = sts.get_caller_identity()["Account"]

    print(f"Using stack: {stack_name}, profile: {profile}, region: {region}")
    usernames = get_usernames(cloudformation, stack_name)
    print(f"Detected the following users: {usernames}")

    if delete:
        for username in usernames:
            try:
                iam.delete_login_profile(UserName=username)
                print(f"Deleted login profile for {username}.")
            except iam.exceptions.NoSuchEntityException:
                print(f"No login profile found for {username}.")
        print("Deletion complete.")
        return

    credentials = []
    login_url = f"https://{account_id}.signin.aws.amazon.com/console"

    for username in usernames:
        credential = create_console_credentials(iam, username)
        credential["Console sign-in URL"] = login_url
        credentials.append(credential)

    csv_file = "credentials.csv"

    with open(csv_file, mode="w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["User name", "Password", "Console sign-in URL"]
        )
        writer.writeheader()
        writer.writerows(credentials)

    print(f"Credentials written to {csv_file}")
    render_pdf(credentials)


if __name__ == "__main__":
    main()
